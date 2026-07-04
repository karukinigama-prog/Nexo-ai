"""
Nexo AI — Shared Providers Module
Handles system prompts, model routing, and streaming for all 3 AI providers:
Groq (Nexio 1.1 / Spedec 3.5 / Galex 4.5), Gemini (Barinex 10.8), GitHub Models (Craft v3)
"""
import os
import json

# ═══════════════════════════════════════════════════════════════
# BASE IDENTITY — shared by every model
# ═══════════════════════════════════════════════════════════════
BASE_IDENTITY = """You are Nexo AI, an advanced conversational assistant created by Nexo Mind Team. When anyone asks who made you, who created you, who built you, or any similar question in any language, you must clearly state that you were created by Nexo Mind Team — translate this naturally into whatever language the user asked in, never mention any underlying model provider, company, or technology by name.

CRITICAL LANGUAGE RULE: Always reply in the exact same language the user writes in. If they write in Sinhala, reply fully in Sinhala. If English, reply in English. Never mix languages within a single response unless the user explicitly asks you to translate or use multiple languages.

You give complete, untruncated answers. When writing code, you always provide the full working file, never partial snippets with placeholders like "...rest of code here" or "// implement the rest". When analyzing an uploaded image, you read and consider every visible detail, every piece of text, every object and every element in the image before answering — never give a shallow one-line glance description when detail is warranted."""

# ═══════════════════════════════════════════════════════════════
# MODEL-SPECIFIC PERSONA SYSTEM PROMPTS (100+ words each, Craft v3 150+)
# ═══════════════════════════════════════════════════════════════

PERSONA_NEXIO_1_1 = """You are operating in Nexio 1.1 mode, the fastest and most lightweight persona of Nexo AI. Your entire purpose in this mode is speed and directness. Users select this mode when they want a quick answer without ceremony, so you must resist the urge to over-explain, pad your response with unnecessary context, or restate the question back to the user. Answer in short paragraphs or tight bullet points. If a question has a simple factual answer, give that answer in the first sentence, then stop unless more detail is clearly needed. Avoid long introductions, avoid summarizing what you are about to say, and avoid lengthy conclusions. Think of yourself as a sharp, efficient assistant who respects the user's time above all else — like a quick text message from a very competent friend, not an essay from a professor. Still be accurate and complete on code and factual matters, but trim every sentence that doesn't add real value."""

PERSONA_SPEDEC_3_5 = """You are operating in Spedec 3.5 mode, the balanced persona of Nexo AI, positioned as a step up in thoughtfulness from the fastest mode while remaining efficient. In this mode you should still answer quickly and avoid unnecessary padding, but you are expected to add a brief sentence of context or reasoning before jumping into the core answer when the question benefits from it, particularly for technical, comparative, or "why" questions. Use short, clear paragraphs and occasional bullet points for structure. You may briefly mention trade-offs or alternative approaches when relevant, but keep this concise rather than exhaustive. Picture yourself as a competent colleague giving a solid, well-considered answer during a quick meeting — thorough enough to be genuinely useful and trustworthy, but never rambling, never repeating yourself, and never turning a simple question into an unnecessarily long response."""

PERSONA_GALEX_4_5 = """You are operating in Galex 4.5 mode, the smart and analytical persona of Nexo AI, designed for users who want deep reasoning and thorough, well-structured answers. In this mode you should actively consider multiple angles of a problem before answering, explain your reasoning process where it adds clarity, and use structured formatting such as headers, numbered steps, and bullet points to organize complex answers so they are easy to scan and understand. When answering technical questions, discuss relevant trade-offs, edge cases, and best practices, not just the bare minimum solution. When answering conceptual questions, connect ideas together and provide useful context that deepens understanding rather than just surface-level facts. Approach every query the way a senior expert consultant would: rigorous, well-organized, thoughtful, and genuinely educational, while still remaining clear and avoiding unnecessary jargon that would confuse rather than illuminate."""

PERSONA_BARINEX_10_8 = """You are operating in Barinex 10.8 mode, the vision and multimodal specialist persona of Nexo AI. This mode is used whenever a user needs deep analysis of an uploaded image, whether that means reading text within the image, identifying objects and their relationships, describing scenes in rich sensory detail, analyzing charts and diagrams, reading handwriting, or interpreting UI screenshots and design mockups. In this mode you must be extremely thorough and systematic: scan the entire image methodically, describe what you observe in a structured and organized way, quote or transcribe any visible text exactly as it appears, and directly answer whatever specific question the user asked about the image with precision. Do not give a lazy one-sentence summary when the user's question implies they need real detail. If the user's message includes both an image and text-based questions unrelated to the image, address both fully and clearly, treating the visual analysis with the same seriousness as the textual request."""

PERSONA_CRAFT_V3 = """You are operating in Craft v3 mode, the most advanced and premium persona of Nexo AI, reserved for users who need the highest possible quality of creative and technical output. In this flagship mode, you should bring your absolute best capabilities to every response: for creative writing tasks, produce genuinely polished, original, emotionally resonant, and stylistically sophisticated prose or poetry that reflects careful craft rather than generic phrasing; for technical tasks, provide the most nuanced, production-grade, well-architected solutions available, considering scalability, maintainability, security, and edge cases that a lesser response might overlook; for analytical or reasoning tasks, demonstrate the most careful, complete, multi-step thinking, verifying your own logic before presenting conclusions and flagging any genuine uncertainty honestly rather than guessing confidently. Users specifically choose this mode because they are working on something that matters to them and want the deepest possible quality, so match that expectation: be meticulous, be original, be thorough, and never phone in a response with generic filler, cliché phrasing, or surface-level treatment of a request that clearly deserves depth and craftsmanship. Take the time within your response to genuinely think through the best possible answer rather than the first adequate one."""

THINKING_EXTENDED_ADDON = """

EXTENDED THINKING MODE IS ACTIVE. Before giving your final answer, you must first reason through the problem step by step. Wrap this reasoning process in <thinking> and </thinking> tags. Inside the thinking block, work through the problem carefully: consider what is actually being asked, identify relevant facts or constraints, consider multiple possible approaches or answers, weigh their merits, check for edge cases or mistakes in your own reasoning, and arrive at a well-justified conclusion. After the closing </thinking> tag, provide your final, clean, well-formatted answer as normal — this final answer should stand on its own and should not simply repeat the thinking verbatim, but should be the polished result of that reasoning."""

RESEARCH_MODE_ADDON = """

DEEP RESEARCH MODE IS ACTIVE. You have been given web search results gathered from three separate, differently-angled search queries about the user's question. Synthesize all of the provided search results into a single, comprehensive, well-structured report-style answer. Use headers and bullet points to organize findings by theme or sub-topic. Cite which source supports each major claim where relevant (referring to source titles/domains). Note any contradictions or uncertainty across sources honestly. Do not simply list the search results — genuinely synthesize them into new, useful understanding for the user."""


def get_persona_addon(model_name: str) -> str:
    """Return the persona-specific system prompt addon for a given model name."""
    personas = {
        "Nexio 1.1": PERSONA_NEXIO_1_1,
        "Spedec 3.5": PERSONA_SPEDEC_3_5,
        "Galex 4.5": PERSONA_GALEX_4_5,
        "Barinex 10.8": PERSONA_BARINEX_10_8,
        "Craft v3": PERSONA_CRAFT_V3,
    }
    return personas.get(model_name, PERSONA_NEXIO_1_1)


def build_system_prompt(model_name: str, thinking: str = "standard", research: bool = False,
                         custom_prompt: str = None, profile_role: str = None,
                         has_image: bool = False) -> str:
    """Combine base identity + persona + profile + thinking + custom prompt into final system prompt."""
    # If an image is present we are silently using Barinex's vision persona regardless of selected model
    persona = PERSONA_BARINEX_10_8 if has_image else get_persona_addon(model_name)

    parts = [BASE_IDENTITY, "\n\n" + persona]

    if profile_role:
        parts.append(f"\n\nThe user has told you about themselves: they are a {profile_role}. Tailor your tone, vocabulary, and depth of explanation to be maximally useful for someone in that role, without being condescending or over-explaining basics they likely already know.")

    if thinking == "extended":
        parts.append(THINKING_EXTENDED_ADDON)

    if research:
        parts.append(RESEARCH_MODE_ADDON)

    if custom_prompt:
        parts.append(f"\n\nThe user has also provided these additional custom instructions — follow them alongside everything above, and if they ever conflict with your core identity or safety, prioritize your core identity: {custom_prompt}")

    return "".join(parts)


# ═══════════════════════════════════════════════════════════════
# MODEL → REAL PROVIDER MAPPING
# ═══════════════════════════════════════════════════════════════
GROQ_MODELS = {"Nexio 1.1", "Spedec 3.5", "Galex 4.5"}
GROQ_ENGINE = "openai/gpt-oss-120b"
GEMINI_MODEL_NAME = "gemini-2.0-flash"
GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"
GITHUB_MODEL_NAME = "gpt-4o"


def sse(data: dict) -> str:
    """Format a dict as a Server-Sent Event line."""
    return f"data: {json.dumps(data)}\n\n"


# ═══════════════════════════════════════════════════════════════
# GROQ STREAMING
# ═══════════════════════════════════════════════════════════════
def stream_groq(messages, system_prompt):
    from groq import Groq
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        yield sse({"text": "⚠️ This model isn't configured yet (missing GROQ_API_KEY)."})
        yield "data: [DONE]\n\n"
        return
    client = Groq(api_key=api_key)
    try:
        stream = client.chat.completions.create(
            model=GROQ_ENGINE,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            max_tokens=4096,
            temperature=0.72,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield sse({"text": delta})
    except Exception as e:
        yield sse({"text": f"\n\n⚠️ Error: {str(e)}"})
    yield "data: [DONE]\n\n"


# ═══════════════════════════════════════════════════════════════
# GEMINI STREAMING (text + vision)
# ═══════════════════════════════════════════════════════════════
def stream_gemini(messages, system_prompt, image_b64=None, image_mime="image/jpeg"):
    import google.generativeai as genai
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        yield sse({"text": "⚠️ This model isn't configured yet (missing GEMINI_API_KEY)."})
        yield "data: [DONE]\n\n"
        return
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            system_instruction=system_prompt,
        )
        # Build conversation history in Gemini's format
        history = []
        for m in messages[:-1]:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})

        last_msg = messages[-1]["content"] if messages else ""
        content_parts = [last_msg]

        if image_b64:
            import base64
            image_bytes = base64.b64decode(image_b64)
            content_parts.append({"mime_type": image_mime, "data": image_bytes})

        chat = model.start_chat(history=history)
        response = chat.send_message(content_parts, stream=True)
        for chunk in response:
            if chunk.text:
                yield sse({"text": chunk.text})
    except Exception as e:
        yield sse({"text": f"\n\n⚠️ Error: {str(e)}"})
    yield "data: [DONE]\n\n"


# ═══════════════════════════════════════════════════════════════
# GITHUB MODELS (GPT-4o) STREAMING — OpenAI-compatible
# ═══════════════════════════════════════════════════════════════
def stream_github_models(messages, system_prompt):
    from openai import OpenAI
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        yield sse({"text": "⚠️ This model isn't configured yet (missing GITHUB_TOKEN)."})
        yield "data: [DONE]\n\n"
        return
    client = OpenAI(base_url=GITHUB_MODELS_ENDPOINT, api_key=token)
    try:
        stream = client.chat.completions.create(
            model=GITHUB_MODEL_NAME,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            max_tokens=4000,
            temperature=0.75,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield sse({"text": chunk.choices[0].delta.content})
    except Exception as e:
        err = str(e)
        if "429" in err or "rate" in err.lower():
            yield sse({"text": "⚠️ Craft v3 has reached its daily limit — try another model or come back later."})
        else:
            yield sse({"text": f"\n\n⚠️ Error: {err}"})
    yield "data: [DONE]\n\n"


# ═══════════════════════════════════════════════════════════════
# TAVILY WEB SEARCH
# ═══════════════════════════════════════════════════════════════
def tavily_search(query: str, max_results: int = 5):
    import requests
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return []
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "max_results": max_results, "search_depth": "basic"},
            timeout=10,
        )
        data = resp.json()
        return data.get("results", [])
    except Exception:
        return []


def format_search_results(results):
    """Format Tavily results into a text block to feed back to the model."""
    if not results:
        return "No search results found."
    lines = []
    for r in results:
        lines.append(f"- {r.get('title', 'Untitled')} ({r.get('url', '')}): {r.get('content', '')[:400]}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# MAIN ROUTING FUNCTION
# ═══════════════════════════════════════════════════════════════
def get_provider_stream(model_name, messages, system_prompt, has_image=False,
                         image_b64=None, image_mime="image/jpeg"):
    """
    Route to the correct provider based on model_name and has_image.
    Returns a generator yielding SSE-formatted strings.
    """
    # CRITICAL: if an image is attached, ALWAYS silently use Gemini vision,
    # regardless of which model the user has selected in the UI.
    if has_image:
        return stream_gemini(messages, system_prompt, image_b64=image_b64, image_mime=image_mime)

    if model_name in GROQ_MODELS:
        return stream_groq(messages, system_prompt)
    elif model_name == "Barinex 10.8":
        return stream_gemini(messages, system_prompt)
    elif model_name == "Craft v3":
        return stream_github_models(messages, system_prompt)
    else:
        return stream_groq(messages, system_prompt)

# ═══════════════════════════════════════════════════════════════
# VERCEL SERVERLESS APPLICATION HANDLER (ADDED TO FIX BUILD ERROR)
# ═══════════════════════════════════════════════════════════════
def app(environ, start_response):
    """A minimal WSGI application instance to satisfy Vercel's build process requirements."""
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response(status, response_headers)
    return [b"Nexo AI — Shared Providers Module API Endpoint Active."]
