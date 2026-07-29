"""Cloud LLM seam for grading (cloud-with-consent posture).

Provider order: Anthropic (claude-opus-5 — strongest Chinese pastoral register)
if ANTHROPIC_API_KEY is set, else OpenAI (the repo's existing provider). Tests
set GRADING_FAKE_RESPONSE and never touch the network.

Reports are confessional documents: they leave the machine ONLY through this
call, only with student consent collected via the assignment instructions
(docs/GRADING.md), and API-tier requests are not used for model training.
"""

from __future__ import annotations

import os

ANTHROPIC_MODEL = os.getenv("GRADING_ANTHROPIC_MODEL", "claude-opus-5")
OPENAI_MODEL = os.getenv("GRADING_OPENAI_MODEL", "gpt-4o")
MAX_TOKENS = 4096


def complete(system: str, user: str) -> str:
    fake = os.getenv("GRADING_FAKE_RESPONSE")
    if fake is not None:
        return fake
    if os.getenv("ANTHROPIC_API_KEY"):
        return _complete_anthropic(system, user)
    if os.getenv("OPENAI_API_KEY"):
        return _complete_openai(system, user)
    raise RuntimeError(
        "No LLM credentials: set ANTHROPIC_API_KEY (preferred) or OPENAI_API_KEY. "
        "Tests may set GRADING_FAKE_RESPONSE instead."
    )


def _complete_anthropic(system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("model declined the request (stop_reason=refusal)")
    text = "".join(block.text for block in response.content if block.type == "text")
    if not text:
        raise RuntimeError(f"empty model response (stop_reason={response.stop_reason})")
    return text


def _complete_openai(system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("empty model response")
    return content
