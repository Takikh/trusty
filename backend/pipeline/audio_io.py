"""
Audio I/O adapter for the live interview.

This module loads the vendored STT/TTS implementation from ``hackathon/audio``.
If anything is missing or audio hardware fails, callers can fall back to the
text mock path.
"""
import asyncio
import importlib.util
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIO_ROOT = Path(os.getenv("AUDIO_ROOT", str(PROJECT_ROOT / "audio"))).resolve()
STT_MODULE_PATH = AUDIO_ROOT / "stt_whisper" / "stt.py"
TTS_MODULE_PATH = AUDIO_ROOT / "tts_kokoro" / "tts.py"

_stt_module = None
_tts_module = None
_load_error = None


def _load_audio_modules():
    global _stt_module, _tts_module, _load_error

    if _stt_module and _tts_module:
        return _stt_module, _tts_module

    try:
        if not STT_MODULE_PATH.exists():
            raise FileNotFoundError(f"Missing STT module: {STT_MODULE_PATH}")
        if not TTS_MODULE_PATH.exists():
            raise FileNotFoundError(f"Missing TTS module: {TTS_MODULE_PATH}")

        stt_spec = importlib.util.spec_from_file_location("hackathon_audio_stt", STT_MODULE_PATH)
        tts_spec = importlib.util.spec_from_file_location("hackathon_audio_tts", TTS_MODULE_PATH)
        if not stt_spec or not stt_spec.loader or not tts_spec or not tts_spec.loader:
            raise ImportError("Could not create audio module import specs")

        stt_module = importlib.util.module_from_spec(stt_spec)
        tts_module = importlib.util.module_from_spec(tts_spec)
        stt_spec.loader.exec_module(stt_module)
        tts_spec.loader.exec_module(tts_module)

        _stt_module = stt_module
        _tts_module = tts_module
        _load_error = None
        return _stt_module, _tts_module
    except Exception as exc:
        _load_error = exc
        return None, None


def audio_available() -> bool:
    stt, tts = _load_audio_modules()
    return bool(stt and tts)


def audio_status() -> str:
    if audio_available():
        return f"real audio enabled via {AUDIO_ROOT}"
    return f"real audio unavailable: {_load_error}"


def preload_audio() -> None:
    stt, tts = _load_audio_modules()
    if not stt or not tts:
        return

    if hasattr(stt, "preload"):
        stt.preload()
    if hasattr(tts, "preload"):
        tts.preload()


async def speak_async(text: str, voice: str | None = None) -> None:
    _, tts = _load_audio_modules()
    if not tts:
        raise RuntimeError(audio_status())
    kwargs = {}
    if voice:
        kwargs["voice"] = voice
    await tts.speak(text, **kwargs)


async def listen_async(timeout: int = 45) -> str:
    stt, _ = _load_audio_modules()
    if not stt:
        raise RuntimeError(audio_status())
    return await stt.listen_once(timeout=timeout)


def speak(text: str, voice: str | None = None) -> None:
    asyncio.run(speak_async(text, voice=voice))


def listen(timeout: int = 45) -> str:
    return asyncio.run(listen_async(timeout=timeout))
