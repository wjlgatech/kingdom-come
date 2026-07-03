"""User-controlled mentor memory (C3, REC-3 ChatGPT transparency pattern):
list what the mentor remembers, forget any single memory. Uses the fake
embedder so deletion's index rebuild is deterministic."""
import os

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.services import vector_memory

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_memory(monkeypatch):
    monkeypatch.setenv("EMBEDDING_FAKE", "1")
    vector_memory.reset()
    yield
    vector_memory.reset()


async def _seed(student_id: str, texts: list[str]) -> None:
    for t in texts:
        await vector_memory.add_memory(student_id, t)


def test_list_memories_empty_and_populated(anyio_backend=None):
    assert client.get("/api/memory/stu-x").json() == {"memories": []}

    import asyncio

    asyncio.run(_seed("stu-x", ["Led morning prayer.", "Father is sick."]))
    body = client.get("/api/memory/stu-x").json()
    assert [m["text"] for m in body["memories"]] == ["Led morning prayer.", "Father is sick."]
    assert [m["index"] for m in body["memories"]] == [0, 1]


def test_delete_memory_removes_and_reindexes():
    import asyncio

    asyncio.run(_seed("stu-x", ["alpha memory", "beta memory", "gamma memory"]))
    res = client.delete("/api/memory/stu-x/1")
    assert res.status_code == 204

    body = client.get("/api/memory/stu-x").json()
    assert [m["text"] for m in body["memories"]] == ["alpha memory", "gamma memory"]

    # The search index was rebuilt: recall still works and the deleted
    # memory can no longer surface.
    recalled = asyncio.run(vector_memory.get_memory("stu-x", "gamma memory", k=3))
    assert "gamma memory" in recalled
    assert "beta memory" not in recalled


def test_delete_memory_unknown_index_is_404():
    assert client.delete("/api/memory/stu-x/0").status_code == 404

    import asyncio

    asyncio.run(_seed("stu-x", ["only one"]))
    assert client.delete("/api/memory/stu-x/5").status_code == 404
    assert client.delete("/api/memory/stu-x/-1").status_code == 404
