"""Voice input endpoints (backend/services/stt.py): the availability chain
(VOICE_FAKE_TEXT → faster-whisper → OpenAI → unavailable) and the transcribe
route's guards. The dev venv has no faster-whisper, which is exactly the
point — the chain must degrade honestly."""
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.services import stt

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("VOICE_FAKE_TEXT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    yield


def test_health_reports_unavailable_without_any_backend():
    assert stt.available() is None or stt.available() == "local"
    if stt.available() is None:
        body = client.get("/api/voice/health").json()
        assert body == {"available": False, "engine": None}
        res = client.post(
            "/api/voice/transcribe",
            content=b"x" * 4096,
            headers={"Content-Type": "audio/webm"},
        )
        assert res.status_code == 503


def test_fake_tier_transcribes_deterministically(monkeypatch):
    monkeypatch.setenv("VOICE_FAKE_TEXT", "Steadiness for the homily.")
    assert client.get("/api/voice/health").json() == {"available": True, "engine": "fake"}
    res = client.post(
        "/api/voice/transcribe",
        content=b"x" * 4096,
        headers={"Content-Type": "audio/webm"},
    )
    assert res.status_code == 200
    assert res.json() == {"text": "Steadiness for the homily."}


def test_header_only_blob_is_rejected(monkeypatch):
    monkeypatch.setenv("VOICE_FAKE_TEXT", "anything")
    res = client.post(
        "/api/voice/transcribe",
        content=b"tiny",
        headers={"Content-Type": "audio/webm"},
    )
    assert res.status_code == 422
    assert "too short" in res.json()["detail"]


def test_openai_tier_selected_when_key_present(monkeypatch):
    if stt.available() == "local":  # a machine with faster-whisper outranks the API tier
        pytest.skip("local whisper installed")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert stt.available() == "openai"
