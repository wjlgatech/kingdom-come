from __future__ import annotations

import os
from collections.abc import AsyncIterator

LLM_MODEL = "gpt-4o-mini"


async def stream_llm_response(prompt: str) -> AsyncIterator[str]:
    fake = os.getenv("LLM_FAKE_RESPONSE")
    if fake is not None:
        for word in fake.split(" "):
            yield word + " "
        return

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set; cannot call LLM")

    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    stream = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    async for event in stream:
        if not event.choices:
            continue
        delta = event.choices[0].delta
        if delta and delta.content:
            yield delta.content
