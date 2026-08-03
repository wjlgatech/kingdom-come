"""Vercel Python Function entrypoint — serves the whole FastAPI app.

Vercel's Python runtime looks for a module-level ASGI callable named `app`.
Everything (Jinja pages, /api/*, /static/*) is routed here by vercel.json, so
the deployed demo runs the same code as `make demo`, with two honest caveats:

1. **No WebSockets.** Vercel Functions don't carry them, so `/ws/chat` never
   connects on the demo. `frontend/chat.js` detects the failed handshake and
   falls back to `POST /api/chat` (backend/api/http_chat.py) — same pipeline,
   whole reply instead of a token stream. Local `make demo` keeps the stream.

2. **In-process state is per-instance.** `prayer._state`, the FAISS index in
   `vector_memory`, and the fakeredis bus all live in the function instance.
   Reads are seeded on cold start (KC_DEMO_SEED=1) so every visitor sees a
   full demo week; writes last only as long as that warm instance. That's the
   right trade for a demo — set KC_PERSIST=1 + a real DATABASE_URL for durable
   ledgers, and run one process (see docs/DEPLOY.md).
"""
from __future__ import annotations

import os

# Demo posture must be set before backend.app imports, because the seed runs at
# module import time. setdefault so Vercel project env vars still win.
os.environ.setdefault("KC_DEMO_SEED", "1")
# No Redis on Vercel. realtime.py falls back to fakeredis when REDIS_URL is
# *unset* — an empty string is not unset, so clear it rather than let the bus
# try to dial "".
if not os.getenv("REDIS_URL"):
    os.environ.pop("REDIS_URL", None)
# Deterministic hash-bucket embeddings: no OpenAI spend on a public demo.
os.environ.setdefault("EMBEDDING_FAKE", "1")

from backend.app import app  # noqa: E402  (env must be set first)

__all__ = ["app"]
