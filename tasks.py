"""
Nexo AI — /api/tasks
Returns current background task statuses for the frontend's task bell dropdown to poll.

NOTE: true async background execution isn't reliable on serverless functions;
this is a best-effort simulation for Phase 1. Tasks are created synchronously
inside chat.py's TASKS list and reported here. In-memory storage resets on
cold start (acceptable Phase 1 limitation).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/api/tasks", methods=["GET"])
@app.route("/", methods=["GET"])
def get_tasks():
    try:
        from chat import TASKS
        return jsonify({"tasks": TASKS})
    except Exception:
        # Cold start / import isolation between serverless functions means
        # chat.py's TASKS list may not be shared with this function's process.
        # Return an empty list gracefully rather than erroring.
        return jsonify({"tasks": []})


# Vercel Python runtime looks for a WSGI `app` object at module level — no app.run() call.
