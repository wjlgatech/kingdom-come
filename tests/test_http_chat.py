"""The HTTP chat fallback (`POST /api/chat`).

This is the transport the public Vercel demo actually uses, because serverless
functions can't carry a WebSocket. It must stay behaviourally equivalent to
`/ws/chat` — same pipeline, same memory, same error discipline — or the demo
stops telling the truth about the product.

Follows the isolated_state fixture pattern: process-global FAISS + Redis state
leaks across tests otherwise.
"""
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


def test_http_chat_returns_memory_reply_and_done():
    client = TestClient(app)
    res = client.post("/api/chat", json={"student_id": "stu-1", "message": "Hello"})
    assert res.status_code == 200
    body = res.json()
    # Chunks are joined verbatim, exactly as the WS client concatenates them —
    # including the trailing separator space. Trimming is the UI's job.
    assert body["reply"].strip() == "Grace and peace."
    assert body["done"] is True
    assert isinstance(body["memory"], list)


def test_http_chat_matches_the_websocket_reply():
    """The two transports must not drift — same pipeline, same words."""
    client = TestClient(app)
    http_reply = client.post(
        "/api/chat", json={"student_id": "stu-parity", "message": "Hello"}
    ).json()["reply"]

    vector_memory.reset()
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"student_id": "stu-parity", "message": "Hello"})
        chunks = []
        while True:
            msg = ws.receive_json()
            if msg.get("done"):
                break
            if "memory" in msg:
                continue
            chunks.append(msg["chunk"])
    assert "".join(chunks) == http_reply


def test_http_chat_second_turn_carries_memory():
    """Memory pills come back on a follow-up, exactly as over the socket."""
    client = TestClient(app)
    client.post("/api/chat", json={"student_id": "stu-2", "message": "I feel called to teach."})
    body = client.post("/api/chat", json={"student_id": "stu-2", "message": "Say more."}).json()
    assert body["memory"], "second turn should surface remembered context"


@pytest.mark.parametrize(
    "payload",
    [
        {"student_id": "", "message": "Hello"},
        {"student_id": "stu-1", "message": ""},
        {"message": "Hello"},
        {"student_id": "stu-1"},
    ],
)
def test_http_chat_rejects_incomplete_payloads(payload):
    client = TestClient(app)
    res = client.post("/api/chat", json=payload)
    # Pydantic rejects missing/empty fields with 422; the handler's own guard
    # returns a 200 body with an error key. Either is a refusal, not a reply.
    if res.status_code == 200:
        assert res.json().get("error")
    else:
        assert res.status_code == 422


def test_http_chat_never_leaks_provider_error_text(monkeypatch):
    """Same discipline as the WS relay: log the cause, return a pastoral line."""
    async def boom(student_id, message):
        raise RuntimeError("sk-secret-key-fragment leaked from internal.host")
        yield  # pragma: no cover  (makes this an async generator)

    monkeypatch.setattr("backend.api.http_chat.handle_chat_ws", boom)
    client = TestClient(app)
    body = client.post("/api/chat", json={"student_id": "s", "message": "hi"}).json()
    assert body["error"] == "The mentor is unavailable right now. Try again in a moment."
    assert "sk-secret" not in str(body)
    assert "internal.host" not in str(body)
