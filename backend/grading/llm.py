"""Grading LLM seam — survival chain, ordered for CORRECTNESS first.

Grading is not chat: comments are 8000-char-report Chinese pastoral prose in a
specific voice, and a wrong register is worse than a slow answer. So unlike
the mentor chain (backend/services/llm_client.py — availability-first), this
chain leads with the strongest model and falls back to free tiers:

  1. Anthropic claude-opus-5 (ANTHROPIC_API_KEY) — best Chinese pastoral register
  2. NVIDIA NIM free tier   (NVIDIA_API_KEY)     — gpt-oss-120b, verified live
     by the mentor chain 2026-06-10 (kimi leaks reasoning into content, glm
     ~35s to first token — both rejected there; same defaults inherited here)
  3. OpenAI                 (OPENAI_API_KEY)

No Ollama tier: a 7b local model can't hold this register, and cloud-with-
consent is the agreed posture (docs/GRADING.md). GRADING_FAKE_RESPONSE
short-circuits everything (tests). Reports are confessional documents: they
leave the machine only through this call, with student consent, and API-tier
requests are not used for provider training.
"""

from __future__ import annotations

import os

ANTHROPIC_MODEL = os.getenv("GRADING_ANTHROPIC_MODEL", "claude-opus-5")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.getenv("GRADING_NIM_MODEL", "openai/gpt-oss-120b")
OPENAI_MODEL = os.getenv("GRADING_OPENAI_MODEL", "gpt-4o")
MAX_TOKENS = 4096


def resolve_chain() -> list[str]:
    """Names of the tiers available in this environment, in call order.

    GRADING_ALLOW_OLLAMA=1 opts into a local-model tier (full-privacy mode:
    reports never leave the machine). It is deliberately opt-in and LAST when
    cloud keys exist — local 7-30b models can't reliably hold this register —
    but with no cloud keys it makes the pipeline fully offline.
    """
    chain = []
    if os.getenv("ANTHROPIC_API_KEY"):
        chain.append("anthropic")
    if os.getenv("NVIDIA_API_KEY"):
        chain.append("nvidia")
    if os.getenv("OPENAI_API_KEY"):
        chain.append("openai")
    if os.getenv("GRADING_ALLOW_OLLAMA") == "1":
        chain.append("ollama")
    return chain


def complete(system: str, user: str) -> str:
    fake = os.getenv("GRADING_FAKE_RESPONSE")
    if fake is not None:
        return fake

    chain = resolve_chain()
    if not chain:
        raise RuntimeError(
            "No LLM credentials: set ANTHROPIC_API_KEY (preferred), NVIDIA_API_KEY "
            "(free tier — build.nvidia.com), or OPENAI_API_KEY. "
            "Tests may set GRADING_FAKE_RESPONSE instead."
        )

    errors: list[str] = []
    for tier in chain:
        try:
            if tier == "anthropic":
                return _complete_anthropic(system, user)
            if tier == "nvidia":
                return _complete_openai_protocol(
                    system, user, base_url=NVIDIA_BASE_URL,
                    api_key=os.environ["NVIDIA_API_KEY"], model=NVIDIA_MODEL,
                )
            if tier == "ollama":
                # Default matches the mentor chain's installed model (free-llm
                # rule: wire the model `ollama list` actually shows, never a
                # wished-for one — an uninstalled default 404s silently).
                return _complete_openai_protocol(
                    system, user,
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                    api_key="ollama", model=os.getenv("GRADING_OLLAMA_MODEL", "qwen2.5:7b"),
                )
            return _complete_openai_protocol(
                system, user, base_url=None,
                api_key=os.environ["OPENAI_API_KEY"], model=OPENAI_MODEL,
            )
        except Exception as exc:  # noqa: BLE001 — any tier failure advances the chain
            errors.append(f"{tier}: {exc}")
    raise RuntimeError("all LLM tiers failed — " + " | ".join(errors))


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


def _complete_openai_protocol(
    system: str, user: str, *, base_url: str | None, api_key: str, model: str
) -> str:
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key, max_retries=0)
    response = client.chat.completions.create(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("empty model response")
    return content
