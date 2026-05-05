import asyncio

import pytest

from backend.services import ai_pipeline, realtime, vector_memory


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch):
    monkeypatch.setenv("EMBEDDING_FAKE", "1")
    monkeypatch.delenv("REDIS_URL", raising=False)
    vector_memory.reset()
    realtime.reset_for_tests()
    yield
    vector_memory.reset()
    realtime.reset_for_tests()


def run(coro):
    return asyncio.run(coro)


async def _collect(student_id, message):
    """Collect chunks (strings only); the memory dict envelope is filtered out."""
    return [item async for item in ai_pipeline.handle_chat_ws(student_id, message) if isinstance(item, str)]


async def _collect_all(student_id, message):
    """Collect all yielded items including the memory dict — for protocol assertions."""
    return [item async for item in ai_pipeline.handle_chat_ws(student_id, message)]


def test_pipeline_streams_chunks_from_llm(monkeypatch):
    async def fake_stream(prompt):
        for word in ["Peace", " be", " with", " you."]:
            yield word

    monkeypatch.setattr(ai_pipeline, "stream_llm_response", fake_stream)

    chunks = run(_collect("stu-1", "How is my prayer life?"))

    assert "".join(chunks) == "Peace be with you."


def test_pipeline_persists_user_and_mentor_messages(monkeypatch):
    async def fake_stream(prompt):
        yield "Walk in patience."

    monkeypatch.setattr(ai_pipeline, "stream_llm_response", fake_stream)

    run(_collect("stu-2", "I feel stuck"))
    saved = run(vector_memory.get_memory("stu-2", "stuck patience", k=10))

    assert any("User: I feel stuck" in s for s in saved)
    assert any("Mentor: Walk in patience." in s for s in saved)


def test_pipeline_uses_prior_memory_in_prompt(monkeypatch):
    captured_prompts: list[str] = []

    async def fake_stream(prompt):
        captured_prompts.append(prompt)
        yield "ack"

    monkeypatch.setattr(ai_pipeline, "stream_llm_response", fake_stream)

    run(_collect("stu-3", "I led a small group last week"))
    run(_collect("stu-3", "What should I focus on next about leading groups?"))

    second_prompt = captured_prompts[1]
    assert "User: I led a small group last week" in second_prompt


def test_pipeline_skips_saving_empty_mentor_response(monkeypatch):
    async def fake_stream(prompt):
        if False:
            yield ""

    monkeypatch.setattr(ai_pipeline, "stream_llm_response", fake_stream)

    run(_collect("stu-4", "hello"))
    saved = run(vector_memory.get_memory("stu-4", "hello", k=10))

    assert any("User: hello" in s for s in saved)
    assert not any(s.startswith("Mentor:") for s in saved)


def test_pipeline_publishes_activity_event(monkeypatch):
    async def fake_stream(prompt):
        yield "ok"

    monkeypatch.setattr(ai_pipeline, "stream_llm_response", fake_stream)
    client = realtime._get_client()
    pubsub = client.pubsub()
    pubsub.subscribe("activity")
    pubsub.get_message(timeout=0.1)

    run(_collect("stu-5", "checking in"))

    msg = pubsub.get_message(timeout=1.0)
    assert msg is not None
    assert b"stu-5" in msg["data"]
    pubsub.close()


def test_pipeline_yields_memory_envelope_first(monkeypatch):
    """Pipeline must yield {memory: [...]} dict before any string chunks."""
    async def fake_stream(prompt):
        yield "ack"

    monkeypatch.setattr(ai_pipeline, "stream_llm_response", fake_stream)

    # First call: memory is empty for a new student.
    items = run(_collect_all("stu-mem", "first ever message"))
    assert isinstance(items[0], dict)
    assert "memory" in items[0]
    assert items[0]["memory"] == []
    assert all(isinstance(x, str) for x in items[1:])

    # Second call: memory should now have the prior turn(s).
    items2 = run(_collect_all("stu-mem", "follow up"))
    assert isinstance(items2[0], dict)
    assert "memory" in items2[0]
    assert len(items2[0]["memory"]) > 0
