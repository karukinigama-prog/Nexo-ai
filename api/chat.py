"""
Nexo AI — /api/chat
SSE streaming endpoint. Routes to Groq / Gemini / GitHub Models based on selected model,
handles thinking mode, research mode (3x Tavily search), image vision, and tool-calling web search.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))
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
    return [
        base,
        f"{base} latest news",
        f"{base} explained analysis",
    ]


def maybe_create_task(user_text):
    """If the message looks like a background task request, log it (best-effort simulation)."""
    lowered = user_text.lower().strip()
    if lowered.startswith("/task ") or " and notify me" in lowered:
        task_id = f"task_{len(TASKS) + 1}"
        TASKS.append({"id": task_id, "title": user_text[:60], "status": "done"})
        # NOTE: true async background execution isn't reliable on serverless;
        # this is a best-effort simulation for Phase 1 — task is marked done immediately
        # since the actual AI response IS the task result in this simplified version.


def needs_search(user_text):
    """Simple heuristic: does this look like a factual/current-events question?"""
    triggers = [
        "today", "latest", "current", "now", "recent", "news", "who is", "what is",
        "when did", "when is", "score", "price", "weather", "happened", "2024", "2025", "2026",
        "දැන්", "අද", "නවතම", "වත්මන්",
    ]
    lowered = user_text.lower()
    return any(t in lowered for t in triggers)


@app.route("/api/chat", methods=["POST"])
@app.route("/", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    messages = data.get("messages", [])
    model = data.get("model", "Nexio 1.1")
    thinking = data.get("thinking", "standard")
    research = data.get("research", False)
    image_b64 = data.get("image")
    image_mime = data.get("image_mime", "image/jpeg")
    custom_prompt = data.get("custom_prompt")
    profile_role = data.get("profile_role")
    has_image = bool(image_b64)

    if messages:
        last_user_msg = messages[-1].get("content", "")
        maybe_create_task(last_user_msg)

    system_prompt = build_system_prompt(
        model_name=model,
        thinking=thinking,
        research=research,
        custom_prompt=custom_prompt,
        profile_role=profile_role,
        has_image=has_image,
    )

    def generate():
        try:
            # ── DEEP RESEARCH MODE: 3 sequential Tavily searches ──
            if research and messages:
                user_question = messages[-1].get("content", "")
                queries = generate_research_queries(user_question)
                all_results = []
                for i, q in enumerate(queries, start=1):
                    yield sse({"researching": f"{i}/3"})
                    results = tavily_search(q, max_results=4)
                    all_results.extend(results)

                search_context = format_search_results(all_results)
                augmented_messages = list(messages)
                augmented_messages[-1] = {
                    "role": "user",
                    "content": f"{user_question}\n\n[Web search results gathered for research:]\n{search_context}",
                }
                for chunk in get_provider_stream(model, augmented_messages, system_prompt,
                                                   has_image=has_image, image_b64=image_b64,
                                                   image_mime=image_mime):
                    yield chunk
                return

            # ── AUTO WEB SEARCH for factual/current questions (Groq models only, via simple pre-search) ──
            if not has_image and messages and needs_search(messages[-1].get("content", "")):
                yield sse({"searching": True})
                user_question = messages[-1].get("content", "")
                results = tavily_search(user_question, max_results=5)
                if results:
                    search_context = format_search_results(results)
                    augmented_messages = list(messages)
                    augmented_messages[-1] = {
                        "role": "user",
                        "content": f"{user_question}\n\n[Web search results:]\n{search_context}\n\nUse these results to answer accurately. Mention that this is based on current web search results.",
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
            yield sse({"text": f"\n\n⚠️ Unexpected error: {str(e)}"})
            yield "data: [DONE]\n\n"

    resp = Response(stream_with_context(generate()), mimetype="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"
    resp.headers["Connection"] = "keep-alive"
    return resp


# Vercel Python runtime looks for a WSGI `app` object at module level — no app.run() call.
