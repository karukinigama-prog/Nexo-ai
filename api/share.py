"""
Nexo AI — /api/share
POST creates a shareable snapshot of a conversation.
GET (with ?id=) renders a stripped-down read-only HTML view of that snapshot.

NOTE: in-memory storage resets on cold start / across serverless invocations;
acceptable for Phase 1, will move to a real database in a later phase.
"""
import uuid
from flask import Flask, request, Response

app = Flask(__name__)

# In-memory share store (Phase 1 limitation — see note above)
SHARES = {}


def render_readonly_html(snapshot):
    messages = snapshot.get("messages", [])
    permission = snapshot.get("permission", "view")
    perm_label = "View only" if permission == "view" else "Can edit"

    rows = ""
    for m in messages:
        role_label = "You" if m["role"] == "user" else "Nexo AI"
        css_class = "user" if m["role"] == "user" else "ai"
        content = m.get("content", "").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        rows += f'<div class="msg {css_class}"><div class="role">{role_label}</div><div class="content">{content}</div></div>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nexo AI — Shared Chat</title>
<style>
  body{{background:#0a0a12;color:#e8e8f5;font-family:'Inter',sans-serif;margin:0;padding:24px;max-width:760px;margin:0 auto}}
  h1{{background:linear-gradient(135deg,#7c3aed,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:22px}}
  .badge{{display:inline-block;padding:4px 12px;border-radius:20px;background:rgba(124,58,237,.18);color:#c4b5fd;font-size:12px;margin-bottom:20px}}
  .msg{{padding:14px 18px;border-radius:14px;margin-bottom:14px;line-height:1.6}}
  .msg.ai{{background:rgba(20,19,38,.9);border:1px solid rgba(139,92,246,.2)}}
  .msg.user{{background:linear-gradient(135deg,#5b21b6,#7c3aed);margin-left:40px}}
  .role{{font-size:11px;opacity:.6;margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em}}
</style></head>
<body>
  <h1>✨ Nexo AI — Shared Conversation</h1>
  <div class="badge">🔗 {perm_label}</div>
  {rows}
</body></html>"""


@app.route("/api/share", methods=["POST"])
def create_share():
    data = request.get_json(force=True)
    messages = data.get("messages", [])
    permission = data.get("permission", "view")

    share_id = uuid.uuid4().hex[:10]
    SHARES[share_id] = {"messages": messages, "permission": permission}

    return {"id": share_id, "url": f"/api/share?id={share_id}"}


@app.route("/api/share", methods=["GET"])
def read_share():
    share_id = request.args.get("id", "")
    snapshot = SHARES.get(share_id)

    if not snapshot:
        return Response(
            "<html><body style='background:#0a0a12;color:#e8e8f5;font-family:sans-serif;padding:40px;text-align:center'>"
            "<h2>⚠️ Shared chat not found or expired</h2>"
            "<p style='color:#9090b8'>This may be because the server restarted (in-memory storage in Phase 1).</p>"
            "</body></html>",
            mimetype="text/html",
            status=404,
        )

    return Response(render_readonly_html(snapshot), mimetype="text/html")


# Vercel Python runtime looks for a WSGI `app` object at module level — no app.run() call.
