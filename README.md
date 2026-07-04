# Nexo AI

A premium AI chatbot web app created by **Nexo Mind Team**, featuring 5 AI model personas, real-time web search, deep research mode, extended thinking chain, image vision, dual-mode voice input, and more.

## Features (Phase 1)

- 🤖 5 models: Nexio 1.1, Spedec 3.5, Galex 4.5 (Groq), Barinex 10.8 (Gemini, vision), Craft v3 (GPT-4o via GitHub Models)
- 🧠 Standard / Extended thinking mode with collapsible reasoning
- 🔬 Deep Research mode (3-step web search synthesis)
- 🔍 Automatic web search for factual/current questions (Tavily)
- 🖼️ Image upload with silent auto-routing to vision model
- 🎤 Dual-mode voice: tap to dictate, hold to enter full voice chat mode
- ⚙️ Settings: custom system prompt, profile role, accent color, font size
- 💬 Full message actions: copy, like/dislike, regenerate, edit (with version pager), read aloud, share/export
- 📌 Sidebar: date-grouped history, search, pin, rename, delete
- 🔗 Shareable read-only chat links (view/edit permission)
- 🕶️ Incognito mode
- 🌗 Light/Dark theme
- 📱 Fully responsive (desktop + mobile)

## Environment Variables Required

| Variable | Where to get it | Cost |
|---|---|---|
| `GROQ_API_KEY` | https://console.groq.com | Free, no card |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey | Free, no card |
| `GITHUB_TOKEN` | https://github.com/settings/tokens (create a Personal Access Token) | Free, no card — used for GPT-4o via [GitHub Models](https://github.com/marketplace/models). Rate limit ~50 requests/day for GPT-4o. |
| `TAVILY_API_KEY` | https://tavily.com | Free tier: 1000 searches/month |

## Local Development (Replit)

1. Add all 4 environment variables above in Replit's **Secrets** tab.
2. Run the app — Replit will detect the Flask apps in `/api` and serve `public/index.html`.

## Deploying to Vercel

1. Push this repository to GitHub.
2. Go to [vercel.com](https://vercel.com) → **New Project** → Import your GitHub repo.
3. In **Environment Variables**, add all 4 keys listed above.
4. Click **Deploy**. Vercel automatically detects `vercel.json` and builds:
   - The Python serverless functions in `/api` (`chat.py`, `share.py`, `tasks.py`)
   - The static frontend in `/public` (`index.html`)
5. Once deployed, your app is live at `https://your-project.vercel.app`.

## Project Structure

```
nexo-ai/
├── api/
│   ├── _providers.py   ← shared: system prompts, model routing, streaming logic
│   ├── chat.py         ← POST /api/chat — main SSE streaming endpoint
│   ├── share.py        ← POST/GET /api/share — shareable read-only links
│   └── tasks.py        ← GET /api/tasks — background task status polling
├── public/
│   └── index.html      ← entire frontend (HTML + CSS + JS, single file)
├── vercel.json          ← Vercel routing configuration
├── requirements.txt
├── .gitignore
└── README.md
```

## Known Phase 1 Limitations

- **In-memory storage**: chat share links and background task status are stored in memory and will reset when a Vercel serverless function has a "cold start." This is acceptable for Phase 1 — a real database will be added in a later phase.
- **Background tasks**: true async execution isn't reliable on serverless functions, so tasks are processed synchronously with immediate "done" status as a best-effort simulation.
- **GitHub Models rate limit**: Craft v3 (GPT-4o) is limited to ~50 requests/day on the free tier. If you hit the limit, the app shows a friendly message suggesting another model.

## Roadmap

- **Phase 2**: Artifacts side panel, multi-file workspace, interactive charts, in-browser code execution sandbox
- **Phase 3**: Persistent long-term memory, simplified terminal access, screen/camera live awareness
