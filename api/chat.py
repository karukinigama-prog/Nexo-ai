"""
Nexo AI — /api/chat
SSE streaming endpoint. Routes to Groq / Gemini / GitHub Models based on selected model,
handles thinking mode, research mode (3x Tavily search), image vision, and tool-calling web search.
"""
import sys
import os
import json

# Add project root directory to sys.path to find _providers.py outside /api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from _providers import (
    build_system_prompt, get_provider_stream, tavily_search,
    format_search_results, sse, GROQ_MODELS, GROQ_ENGINE,
)

from flask import Flask, request, Response, stream_with_context

app = Flask(__name__)

# In-memory task store shared across warm invocations (resets on cold start — Phase 1 limitation)
TASKS = []


def generate_research_queries(user_question):
    """Derive 3 differently-angled search queries from the user's question (simple heuristic)."""
    base = user_question.strip().rstrip("?")
    return [\n        base,\n        f"{base} latest news",\n        f"{base} explained analysis",\n    ]


def maybe_create_task(user_text):
    """If the message looks like a background task request, log it (best-effort simulation)."""
    lowered = user_text.lower().strip()
    if lowered.startswith("/task ") or " and notify me" in lowered:
        task_id = f"task_{len(TASKS) + 1}"
        TASKS.append({"id": task_id, "title": user_text[:60], "status": "done"})
        # NOTE: true async background execution isn't reliable on serverless functions, so tasks are fake-sync.


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    model = data.get("model", "Nexio 1.1")
    messages = data.get("messages", [])
    thinking = data.get("thinking", "standard")  # standard or extended
    research = data.get("research", False)
    custom_prompt = data.get("customPrompt", None)
    profile_role = data.get("profileRole", None)

    # Multi-modal detection (if any message has an attached image)
    has_image = data.get("hasImage", False)
    image_b64 = data.get("imageB64", None)
    image_mime = data.get("imageMime", "image/jpeg")

    if not messages:
        return {"error": "No messages provided"}, 400

    user_question = messages[-1]["content"] if messages else ""
    maybe_create_task(user_question)

    # Build the specialized system prompt layer using our shared helper
    system_prompt = build_system_prompt(
        model_name=model,
        thinking=thinking,
        research=research,
        custom_prompt=custom_prompt,
        profile_role=profile_role,
        has_image=has_image
    )

    def generate():
        try:
            # ── DEEP RESEARCH MODE ──
            if research and not has_image:
                queries = generate_research_queries(user_question)
                yield sse({"text": "🔍 *Running deep multi-angle research search...*\\n"})
                
                all_results = []
                for q in queries:
                    results = tavily_search(q, max_results=3)
                    all_results.extend(results)
                
                if not all_results:
                    yield sse({"text": "⚠️ *Web search yielded no results. Proceeding with base knowledge...*\\n\\n"})
                else:
                    search_context = format_search_results(all_results)
                    augmented_messages = list(messages)
                    augmented_messages[-1] = {
                        "role": "user",
                        "content": f"{user_question}\\n\\n[Web search results gathered for report synthesis:]\\n{search_context}\\n\\nSynthesize these multi-angle sources fully into your response.",
                    }
                    for chunk in get_provider_stream(model, augmented_messages, system_prompt):
                        yield chunk
                    return

            # ── AUTO TOOL-CALLING WEB SEARCH (Fallback for standard queries that need current facts) ──
            # Very primitive intent detection for Phase 1
            trigger_words = {"today", "weather", "news", "latest", "current", "stock price", "vs", "2024", "2025", "2026"}
            needs_search = any(w in user_question.lower() for w in trigger_words)

            if needs_search and not research and not has_image:
                yield sse({"text": "🔍 *Searching the web...*\\n"})
                results = tavily_search(user_question, max_results=4)
                if results:
                    search_context = format_search_results(results)
                    augmented_messages = list(messages)
                    augmented_messages[-1] = {
                        "role": "user",
                        "content": f"{user_question}\\n\\n[Web search results:]\\n{search_context}\\n\\nUse these results to answer accurately. Mention that this is based on current web search results.",
                    }
                    for chunk in get_provider_stream(model, augmented_messages, system_prompt,
                                                       has_image=has_image, image_b64=image_b64,
                                                       image_mime=image_mime):
                        yield chunk
                    return

            # ── NORMAL FLOW ──
            for chunk in get_provider_stream(model, messages, system_prompt,
                                               has_image=has_image, image_b64=image_b64,
                                               image_mime=image_mime):
                yield chunk

        except Exception as e:
            yield sse({"text": f"\\n\\n⚠️ Unexpected error: {str(e)}"})
            yield "data: [DONE]\\n\\n"

    resp = Response(stream_with_context(generate()), mimetype="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"
    resp.headers["Connection"] = "keep-alive"
    return resp


# Vercel Python runtime looks for a WSGI `app` object at module level — no app.run() call.
