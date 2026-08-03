"""HTTP fallback for the mentor chat — one request, one whole reply.

The WebSocket at `/ws/chat` is the primary transport and stays the power path:
it streams token-by-token and keeps the socket open across turns. But serverless
hosts (Vercel Functions among them) don't carry WebSockets, so on the public
demo the socket can never open and the chat surface would be dead.

This endpoint drains the exact same `handle_chat_ws` generator and returns its
three parts as one JSON body, preserving the WS contract's *ordering* semantics
as structure:

    {"memory": [...], "reply": "...", "done": true}

The client renders memory pills first, then the reply — same UI, no streaming.
Keep the two transports fed by the same pipeline; if they ever diverge, the
demo stops telling the truth about the product.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.ai_pipeline import handle_chat_ws

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    student_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


@router.post("/api/chat")
async def http_chat(payload: ChatRequest) -> dict:
    student_id = payload.student_id.strip()
    message = payload.message.strip()
    if not student_id or not message:
        return {"error": "student_id and message are required"}

    memory: list = []
    chunks: list[str] = []
    try:
        async for item in handle_chat_ws(student_id, message):
            if isinstance(item, dict):
                if "memory" in item:
                    memory = item["memory"]
            else:
                chunks.append(item)
    except Exception:
        # Same discipline as the WS relay: log the real cause, never echo
        # provider error text (it can embed key fragments / internal hosts).
        logger.exception("chat pipeline error for student_id=%s", student_id)
        return {"error": "The mentor is unavailable right now. Try again in a moment."}

    return {"memory": memory, "reply": "".join(chunks), "done": True}
