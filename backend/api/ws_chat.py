from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.ai_pipeline import handle_chat_ws

logger = logging.getLogger(__name__)
router = APIRouter()


async def _relay_reply(websocket: WebSocket, student_id: str, message: str) -> None:
    """Stream one mentor reply over the socket: memory dict, chunks, then done."""
    try:
        async for item in handle_chat_ws(student_id, message):
            if isinstance(item, dict):
                await websocket.send_json(item)
            else:
                await websocket.send_json({"chunk": item})
        await websocket.send_json({"done": True})
    except Exception:
        # Log the real cause server-side; never echo provider error
        # text (which can embed redacted key fragments / internal
        # hostnames) to the client.
        logger.exception("chat pipeline error for student_id=%s", student_id)
        await websocket.send_json({"error": "The mentor is unavailable right now. Try again in a moment."})


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            student_id = (data.get("student_id") or "").strip() if isinstance(data, dict) else ""
            message = (data.get("message") or "").strip() if isinstance(data, dict) else ""
            if not student_id or not message:
                await websocket.send_json({"error": "student_id and message are required"})
                continue
            await _relay_reply(websocket, student_id, message)
    except WebSocketDisconnect:
        return
