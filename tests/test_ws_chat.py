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
    memory = None
    while True:
        msg = ws.receive_json()
        if msg.get("done"):
            return chunks, None, memory
        if "error" in msg:
            return chunks, msg["error"], memory
        if "memory" in msg:
            memory = msg["memory"]
            continue
        chunks.append(msg["chunk"])


def test_ws_streams_chunks_and_completes():
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"student_id": "stu-1", "message": "Hello"})
        chunks, error, _ = _drain_until_done(ws)

    assert error is None
    assert "".join(chunks).strip() == "Grace and peace."


def test_ws_rejects_missing_fields_without_closing():
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"student_id": "", "message": ""})
        first = ws.receive_json()
        assert "error" in first

        ws.send_json({"student_id": "stu-2", "message": "ok"})
        chunks, error, _ = _drain_until_done(ws)
        assert error is None
        assert "Grace" in "".join(chunks)


def test_ws_handles_consecutive_messages_for_same_student():
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"student_id": "stu-3", "message": "first"})
        _drain_until_done(ws)
        ws.send_json({"student_id": "stu-3", "message": "second"})
        chunks, error, _ = _drain_until_done(ws)

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


def test_ws_emits_memory_envelope_before_chunks():
    """The memory envelope must arrive before any chunks so the UI can render
    'Mentor remembers:' pills above the streamed bubble."""
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as ws:
        # First send: empty memory expected (new student).
        ws.send_json({"student_id": "stu-mem-1", "message": "First reflection: feeling uncertain."})
        first = ws.receive_json()
        assert "memory" in first
        assert first["memory"] == []
        chunks, error, _ = _drain_until_done(ws)
        assert error is None and "Grace" in "".join(chunks)

        # Second send: memory should now contain the prior turn(s).
        ws.send_json({"student_id": "stu-mem-1", "message": "Following up on uncertainty."})
        first2 = ws.receive_json()
        assert "memory" in first2
        assert isinstance(first2["memory"], list)
        assert len(first2["memory"]) > 0
        # Order: memory MUST be the first message — assert by also confirming
        # no chunk was sent before it (we just received it as message #1).
        chunks2, error2, _ = _drain_until_done(ws)
        assert error2 is None
