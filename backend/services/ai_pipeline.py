from __future__ import annotations

from collections.abc import AsyncIterator

from .event_engine import process_events
from .llm_client import stream_llm_response
from .prompt_builder import build_prompt
from .vector_memory import add_memory, get_memory


async def handle_chat_ws(student_id: str, message: str) -> AsyncIterator[str]:
    memory = await get_memory(student_id, message)
    prompt = build_prompt(memory, message)

    response_chunks: list[str] = []
    async for chunk in stream_llm_response(prompt):
        response_chunks.append(chunk)
        yield chunk

    full_response = "".join(response_chunks).strip()
    await add_memory(student_id, f"User: {message}")
    if full_response:
        await add_memory(student_id, f"Mentor: {full_response}")
    process_events(student_id, message)
