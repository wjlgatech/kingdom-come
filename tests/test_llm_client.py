"""Fallback chain for the mentor LLM backend (free-llm survival-chain rule).

Order: NVIDIA NIM (free) → local Ollama (always wired, skipped fast when the
daemon is down) → OpenRouter → OpenAI. LLM_FAKE_RESPONSE short-circuits
everything; LLM_MODEL overrides only the primary tier's model. A tier that
fails before yielding advances the chain; a mid-stream failure re-raises so
two providers' text is never spliced together.
"""
import pytest

from backend.services import llm_client


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in (
        "NVIDIA_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY",
        "OLLAMA_MODEL", "OLLAMA_BASE_URL", "LLM_MODEL", "LLM_FAKE_RESPONSE",
    ):
        monkeypatch.delenv(var, raising=False)


def test_full_chain_order(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    chain = llm_client.resolve_chain()
    assert [t["name"] for t in chain] == ["nvidia", "ollama", "openrouter", "openai"]
    assert chain[0]["base_url"] == llm_client.NVIDIA_BASE_URL
    assert chain[0]["model"] == llm_client.NVIDIA_DEFAULT_MODEL
    assert chain[-1]["base_url"] is None  # OpenAI default endpoint


def test_ollama_is_always_wired_even_with_no_keys():
    chain = llm_client.resolve_chain()
    assert [t["name"] for t in chain] == ["ollama"]
    assert chain[0]["model"] == llm_client.OLLAMA_DEFAULT_MODEL


def test_llm_model_overrides_primary_tier_only(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "z-ai/glm-5.1")
    chain = llm_client.resolve_chain()
    assert chain[0]["model"] == "z-ai/glm-5.1"
    assert chain[-1]["model"] == llm_client.OPENAI_DEFAULT_MODEL


def test_ollama_model_env_overrides_local_default(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:latest")
    chain = llm_client.resolve_chain()
    assert chain[0]["model"] == "llama3.1:latest"


@pytest.mark.anyio
async def test_fake_response_short_circuits_the_chain(monkeypatch):
    monkeypatch.setenv("LLM_FAKE_RESPONSE", "Peace be with you.")
    chunks = [c async for c in llm_client.stream_llm_response("anything")]
    assert "".join(chunks).strip() == "Peace be with you."


@pytest.mark.anyio
async def test_failed_tier_advances_to_next(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    calls = []

    async def fake_stream(tier, prompt):
        calls.append(tier["name"])
        if tier["name"] == "nvidia":
            raise ConnectionError("429 simulated throttle")
        yield "from-"
        yield tier["name"]

    monkeypatch.setattr(llm_client, "_stream_from", fake_stream)
    chunks = [c async for c in llm_client.stream_llm_response("hi")]
    assert calls == ["nvidia", "ollama"]
    assert "".join(chunks) == "from-ollama"


@pytest.mark.anyio
async def test_midstream_failure_reraises_instead_of_splicing(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")

    async def fake_stream(tier, prompt):
        yield "half a reply "
        raise ConnectionError("died mid-stream")

    monkeypatch.setattr(llm_client, "_stream_from", fake_stream)
    received = []
    with pytest.raises(ConnectionError):
        async for chunk in llm_client.stream_llm_response("hi"):
            received.append(chunk)
    assert received == ["half a reply "]


@pytest.mark.anyio
async def test_all_tiers_failing_raises_runtime_error(monkeypatch):
    async def fake_stream(tier, prompt):
        raise ConnectionError(f"{tier['name']} down")
        yield  # pragma: no cover — makes this an async generator

    monkeypatch.setattr(llm_client, "_stream_from", fake_stream)
    with pytest.raises(RuntimeError, match="all LLM backends failed"):
        async for _ in llm_client.stream_llm_response("hi"):
            pass
