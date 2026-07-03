"""WebSocket for the in-app Copilot (see backend/services/copilot.py).

Contract mirrors /ws/chat: the client sends {role, question, student_id?};
the server yields {"context": [tool names]} first (so the UI can render the
"Consulted:" pills before any text), then {"chunk": ...} frames, then
{"done": true}. Errors come back as {"error": ...} without closing the
socket.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services import copilot

logger = logging.getLogger(__name__)
router = APIRouter()


async def _relay_answer(websocket: WebSocket, role: str, question: str, student_id: str | None) -> None:
    try:
        async for item in copilot.answer(role, question, student_id=student_id):
            if isinstance(item, dict):
                await websocket.send_json(item)
            else:
                await websocket.send_json({"chunk": item})
        await websocket.send_json({"done": True})
    except Exception:
        # Same rule as ws_chat: log the real cause server-side, never echo
        # provider error text (key fragments, hostnames) to the client.
        logger.exception("copilot error for role=%s", role)
        await websocket.send_json({"error": "The guide is unavailable right now. Try again in a moment."})


@router.websocket("/ws/copilot")
async def websocket_copilot(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            role = (data.get("role") or "").strip() if isinstance(data, dict) else ""
            question = (data.get("question") or "").strip() if isinstance(data, dict) else ""
            student_id = (data.get("student_id") or "").strip() or None if isinstance(data, dict) else None
            if role not in ("seminarian", "director") or not question:
                await websocket.send_json({"error": "role (seminarian|director) and question are required"})
                continue
            if role == "seminarian" and not student_id:
                await websocket.send_json({"error": "student_id is required for the seminarian scope"})
                continue
            await _relay_answer(websocket, role, question, student_id)
    except WebSocketDisconnect:
        return
