from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import TypedDict

# Mentor LLM backend with a survival chain (free-llm skill standing rule):
# free tiers throttle and die mid-conversation, so the chat never depends on
# one provider. Tiers, in order, included when their prerequisite exists:
#
#   1. NVIDIA NIM   (free, frontier-class)      — NVIDIA_API_KEY
#   2. local Ollama (free, offline-proof)       — always wired; skipped fast
#                                                 when the daemon isn't up
#   3. OpenRouter   (paid credits)              — OPENROUTER_API_KEY
#   4. OpenAI       (paid)                      — OPENAI_API_KEY
#
# All four speak the OpenAI protocol, so one AsyncOpenAI client serves the
# whole chain. LLM_FAKE_RESPONSE still short-circuits everything (tests).
#
# Default NIM model verified live 2026-06-10 against the app's real prompt:
# gpt-oss-120b answers in ~3s, clean and on-register. Rejected after testing:
# kimi-k2.6 leaks chain-of-thought into delta.content (reasoning monologue
# reaches the chat bubble); glm-5.1 takes ~35s to first token;
# deepseek-v4-flash timed out. Override the primary tier's model with LLM_MODEL.
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_DEFAULT_MODEL = "openai/gpt-oss-120b"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_DEFAULT_MODEL = "qwen2.5:7b"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_DEFAULT_MODEL = "openai/gpt-5-mini"
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"


class Tier(TypedDict):
    name: str
    base_url: str | None  # None = OpenAI's default endpoint
    api_key: str
    model: str


def resolve_chain() -> list[Tier]:
    """Build the fallback chain from the environment. LLM_MODEL overrides the
    model of the *primary* tier only — lower tiers keep their own defaults
    (a local Ollama can't run a NIM model id)."""
    chain: list[Tier] = []
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        chain.append(
            {"name": "nvidia", "base_url": NVIDIA_BASE_URL, "api_key": nvidia_key,
             "model": NVIDIA_DEFAULT_MODEL}
        )
    chain.append(
        {"name": "ollama", "base_url": os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL),
         "api_key": "ollama", "model": os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)}
    )
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        chain.append(
            {"name": "openrouter", "base_url": OPENROUTER_BASE_URL, "api_key": openrouter_key,
             "model": os.getenv("OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)}
        )
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        chain.append(
            {"name": "openai", "base_url": None, "api_key": openai_key,
             "model": OPENAI_DEFAULT_MODEL}
        )
    model_override = os.getenv("LLM_MODEL")
    if model_override and chain:
        chain[0]["model"] = model_override
    return chain


async def _stream_from(tier: Tier, prompt: str) -> AsyncIterator[str]:
    from openai import AsyncOpenAI

    # `async with` closes the underlying httpx pool when the tier finishes or
    # fails, so a long-running process doesn't leak a socket per chat message.
    async with AsyncOpenAI(
        base_url=tier["base_url"],
        api_key=tier["api_key"],
        timeout=float(os.getenv("KC_LLM_TIMEOUT_S", "45")),
        max_retries=0,  # the chain is the retry policy
    ) as client:
        # Constrained sampling: the mentor speaks in 2-4 sentences; without a
        # max_tokens cap, free-tier models wander into multi-page rambles.
        stream = await client.chat.completions.create(
            model=tier["model"],
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            temperature=0.6,
            max_tokens=400,
        )
        async for event in stream:
            if not event.choices:
                continue
            delta = event.choices[0].delta
            if delta and delta.content:
                yield delta.content


async def stream_llm_response(prompt: str) -> AsyncIterator[str]:
    fake = os.getenv("LLM_FAKE_RESPONSE")
    if fake is not None:
        for word in fake.split(" "):
            yield word + " "
        return

    last_error: Exception | None = None
    for tier in resolve_chain():
        yielded = False
        try:
            async for chunk in _stream_from(tier, prompt):
                yielded = True
                yield chunk
        except Exception as exc:  # noqa: BLE001 — any tier failure advances the chain
            if yielded:
                # Mid-stream death: re-raise rather than splice a second
                # provider's reply onto a half-finished one.
                raise
            last_error = exc
            continue
        return
    raise RuntimeError(f"all LLM backends failed (last: {last_error})")
