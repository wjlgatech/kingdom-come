import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.services import realtime, vector_memory


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch):
    monkeypatch.setenv("EMBEDDING_FAKE", "1")
    monkeypatch.setenv("LLM_FAKE_RESPONSE", "Grace and peace.")
    monkeypatch.delenv("REDIS_URL", raising=False)
    vector_memory.reset()
    realtime.reset_for_tests()
    yield
    vector_memory.reset()
    realtime.reset_for_tests()


def _drain_until_done(ws):
    chunks = []
    while True:
        msg = ws.receive_json()
        if msg.get("done"):
            return chunks, None
        if "error" in msg:
            return chunks, msg["error"]
        chunks.append(msg["chunk"])


def test_ws_streams_chunks_and_completes():
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"student_id": "stu-1", "message": "Hello"})
        chunks, error = _drain_until_done(ws)

    assert error is None
    assert "".join(chunks).strip() == "Grace and peace."


def test_ws_rejects_missing_fields_without_closing():
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"student_id": "", "message": ""})
        first = ws.receive_json()
        assert "error" in first

        ws.send_json({"student_id": "stu-2", "message": "ok"})
        chunks, error = _drain_until_done(ws)
        assert error is None
        assert "Grace" in "".join(chunks)


def test_ws_handles_consecutive_messages_for_same_student():
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"student_id": "stu-3", "message": "first"})
        _drain_until_done(ws)
        ws.send_json({"student_id": "stu-3", "message": "second"})
        chunks, error = _drain_until_done(ws)

    assert error is None
    assert "Grace" in "".join(chunks)


def test_ws_disconnect_does_not_propagate_error():
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"student_id": "stu-4", "message": "bye"})
        _drain_until_done(ws)
    # Reaching here without exception is the assertion.


def test_ws_pipeline_error_is_surfaced_as_json(monkeypatch):
    from backend.api import ws_chat

    async def boom(student_id, message):
        raise RuntimeError("simulated upstream failure")
        yield  # pragma: no cover

    monkeypatch.setattr(ws_chat, "handle_chat_ws", boom)

    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"student_id": "stu-5", "message": "trigger"})
        msg = ws.receive_json()

    assert "error" in msg
    assert "simulated upstream failure" in msg["error"]
