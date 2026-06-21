"""Voice transcription via OpenAI Whisper (brief §7, P2).

Claude doesn't transcribe audio, so voice notes go through Whisper first; the
transcript is shown back to the user before anything is written. The client is
injectable so tests can pass a fake without the SDK or an API key.
"""

from __future__ import annotations

import io
from typing import Any

from app.config import get_settings


async def transcribe(audio: bytes, filename: str = "voice.ogg", client: Any = None) -> str:
    settings = get_settings()
    if client is None:  # pragma: no cover - exercised only with a real key
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)

    buf = io.BytesIO(audio)
    buf.name = filename
    resp = await client.audio.transcriptions.create(model=settings.whisper_model, file=buf)
    return (getattr(resp, "text", "") or "").strip()
