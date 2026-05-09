# The Pria Project
# voice.py
# Handles speech input (Whisper) and speech output (Kokoro).
# Imported by demiurge.py and api.py.
# All voice logic lives here so demiurge and api stay clean.

import io
import numpy as np
import sounddevice as sd
import soundfile as sf

# ─── OUTPUT — KOKORO ──────────────────────────────────────────────────────────

_kokoro = None

def _get_kokoro():
    """Lazy-loads Kokoro on first use."""
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
    return _kokoro


def speak(text: str, voice: str = "af_heart", speed: float = 1.0):
    """
    Speaks text aloud via Kokoro.
    Skips empty or whitespace-only text.
    """
    if not text or not text.strip():
        return
    try:
        kokoro = _get_kokoro()
        samples, sample_rate = kokoro.create(text, voice=voice, speed=speed, lang="en-us")
        sd.play(samples, sample_rate)
        sd.wait()
    except Exception as e:
        print(f"[VOICE] Output error: {e}")


def speak_to_bytes(text: str, voice: str = "af_heart", speed: float = 1.0) -> bytes:
    """
    Generates speech and returns raw WAV bytes.
    Used by api.py to send audio to the phone.
    """
    if not text or not text.strip():
        return b""
    try:
        kokoro = _get_kokoro()
        samples, sample_rate = kokoro.create(text, voice=voice, speed=speed, lang="en-us")
        buf = io.BytesIO()
        sf.write(buf, samples, sample_rate, format="WAV")
        buf.seek(0)
        return buf.read()
    except Exception as e:
        print(f"[VOICE] Output error: {e}")
        return b""


# ─── INPUT — WHISPER ──────────────────────────────────────────────────────────

_whisper_model = None

def _get_whisper():
    """Lazy-loads Whisper on first use."""
    global _whisper_model
    if _whisper_model is None:
        import whisper
        _whisper_model = whisper.load_model("base")
    return _whisper_model


def listen(duration: int = 8, sample_rate: int = 16000) -> str:
    """
    Records audio for up to duration seconds and transcribes via Whisper.
    Returns transcribed text, or empty string on failure.
    Press Enter to stop recording early.
    """
    print("[Listening... press Enter to stop]")
    try:
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        input()  # Enter stops recording early
        sd.stop()

        audio = recording.flatten()

        model = _get_whisper()
        result = model.transcribe(audio, fp16=False)
        text = result.get("text", "").strip()
        return text
    except Exception as e:
        print(f"[VOICE] Input error: {e}")
        return ""