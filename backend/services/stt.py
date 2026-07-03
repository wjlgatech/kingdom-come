"""Speech-to-text for voice input — same stack as dreammaketrue's /voice
(MediaRecorder in the browser → one POST → faster-whisper on the server),
adapted to this repo's fallback-chain convention:

    VOICE_FAKE_TEXT (tests, demos)  →  faster-whisper (local, free, [voice]
    extra)  →  OpenAI Whisper API (OPENAI_API_KEY)  →  unavailable

`available()` names the live tier so the UI can hide the mic entirely when
nothing can transcribe — a dead mic button is worse than none.

Privacy note: unlike the reference implementation, no audio is ever written
to a debug file — this app carries prayer; voice clips are transcribed from
a temp file that is deleted in `finally`, and never logged.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
from functools import lru_cache

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny/base run fine on CPU


@lru_cache(maxsize=1)
def _local_model() -> object | None:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    return WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")


def available() -> str | None:
    """Which transcription tier is live: 'fake' | 'local' | 'openai' | None."""
    if os.getenv("VOICE_FAKE_TEXT"):
        return "fake"
    if _local_model() is not None:
        return "local"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return None


async def transcribe(audio_bytes: bytes) -> str:
    """Audio bytes (webm/mp4/wav — anything ffmpeg decodes) → text.

    Returns "" when no speech is detected; raises RuntimeError when no tier
    is available (callers should have checked available() / hidden the mic).
    """
    tier = available()
    if tier == "fake":
        return os.environ["VOICE_FAKE_TEXT"]
    if tier == "local":
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _transcribe_local, audio_bytes)
    if tier == "openai":
        return await _transcribe_openai(audio_bytes)
    raise RuntimeError("no speech-to-text backend available")


def _transcribe_local(audio_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
    try:
        model = _local_model()
        segments, _ = model.transcribe(
            tmp_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        if not text:
            # The VAD's energy gate can eat quiet-but-real speech whole; a
            # no-VAD retry costs one extra pass only on the empty path.
            segments, _ = model.transcribe(tmp_path, beam_size=5)
            text = " ".join(seg.text.strip() for seg in segments).strip()
        return text
    finally:
        import contextlib

        with contextlib.suppress(OSError):
            os.unlink(tmp_path)


async def _transcribe_openai(audio_bytes: bytes) -> str:
    import io

    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    buf = io.BytesIO(audio_bytes)
    buf.name = "voice.webm"  # the SDK infers format from the filename
    result = await client.audio.transcriptions.create(model="whisper-1", file=buf)
    return (result.text or "").strip()
