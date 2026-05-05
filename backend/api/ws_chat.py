from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.ai_pipeline import handle_chat_ws

router = APIRouter()


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
            try:
                async for item in handle_chat_ws(student_id, message):
                    if isinstance(item, dict):
                        await websocket.send_json(item)
                    else:
                        await websocket.send_json({"chunk": item})
                await websocket.send_json({"done": True})
            except Exception as exc:
                await websocket.send_json({"error": f"pipeline error: {exc}"})
    except WebSocketDisconnect:
        return
