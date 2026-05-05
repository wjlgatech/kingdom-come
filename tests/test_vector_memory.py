import asyncio

import pytest

from backend.services import vector_memory


@pytest.fixture(autouse=True)
def fake_embeddings(monkeypatch):
    monkeypatch.setenv("EMBEDDING_FAKE", "1")
    vector_memory.reset()
    yield
    vector_memory.reset()


def run(coro):
    return asyncio.run(coro)


def test_get_memory_returns_empty_for_unknown_student():
    assert run(vector_memory.get_memory("ghost", "anything")) == []


def test_add_then_get_returns_added_text():
    run(vector_memory.add_memory("stu-1", "Studying mission theology"))
    results = run(vector_memory.get_memory("stu-1", "mission theology"))

    assert "Studying mission theology" in results


def test_per_student_isolation_prevents_cross_leak():
    run(vector_memory.add_memory("stu-A", "Alice loves evangelism"))
    run(vector_memory.add_memory("stu-B", "Bob is studying liturgy"))

    a_results = run(vector_memory.get_memory("stu-A", "evangelism"))
    b_results = run(vector_memory.get_memory("stu-B", "evangelism"))

    assert a_results == ["Alice loves evangelism"]
    assert b_results == ["Bob is studying liturgy"]


def test_get_memory_returns_top_k_capped_to_available():
    for i in range(3):
        run(vector_memory.add_memory("stu-3", f"Memory item {i} about evangelism"))

    results = run(vector_memory.get_memory("stu-3", "evangelism", k=10))

    assert len(results) == 3


def test_get_memory_orders_by_relevance():
    run(vector_memory.add_memory("stu-r", "morning prayer routine"))
    run(vector_memory.add_memory("stu-r", "evangelism field practice plan"))
    run(vector_memory.add_memory("stu-r", "weekly liturgy reading"))

    top = run(vector_memory.get_memory("stu-r", "evangelism field practice", k=1))

    assert top == ["evangelism field practice plan"]


def test_empty_text_is_noop():
    run(vector_memory.add_memory("stu-x", ""))
    run(vector_memory.add_memory("stu-x", "   "))

    assert run(vector_memory.get_memory("stu-x", "anything")) == []


def test_empty_query_returns_empty_list():
    run(vector_memory.add_memory("stu-q", "some content"))

    assert run(vector_memory.get_memory("stu-q", "")) == []
    assert run(vector_memory.get_memory("stu-q", "   ")) == []
