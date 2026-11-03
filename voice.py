# The Pria Project
# voice.py
# Handles speech input (Whisper) and speech output (Kokoro).
# Non-blocking queued speech with emotional cadence mapping.

import io
import queue
import threading
from typing import Optional

import sounddevice as sd
import soundfile as sf

# ─── OUTPUT — KOKORO ──────────────────────────────────────────────────────────

_kokoro = None

def _get_kokoro():
    """Lazy-loads Kokoro on first use."""
    global _kokoro

    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(
            "kokoro-v1.0.onnx",
            "voices-v1.0.bin"
        )

        print("✅ Kokoro loaded successfully!")

    return _kokoro


# ─── EMOTION → CADENCE MAPPING ───────────────────────────────────────────────

EMOTION_SPEED = {
    "happy": 1.05,
    "joy": 1.08,
    "excited": 1.10,
    "angry": 1.06,
    "curious": 1.02,

    "sad": 0.90,
    "melancholy": 0.88,
    "lonely": 0.90,
    "tired": 0.85,

    "affection": 0.95,
    "peaceful": 0.92,
    "contentment": 0.95,
}


def _emotion_speed(base_speed: float, emotion: Optional[str]) -> float:
    """Adjusts speech cadence based on emotional state."""

    if not emotion:
        return base_speed

    modifier = EMOTION_SPEED.get(emotion.lower(), 1.0)

    return max(0.7, min(1.25, base_speed * modifier))


# ─── NONBLOCKING SPEECH QUEUE ────────────────────────────────────────────────

_speech_queue = queue.Queue()
_worker_started = False


def _tts_worker():
    """Background worker for speech playback."""

    while True:
        item = _speech_queue.get()

        if item is None:
            break

        try:
            _speak_blocking(**item)
        except Exception as e:
            print(f"[VOICE] Worker error: {e}")


def _start_worker():
    """Starts TTS worker thread once."""

    global _worker_started

    if _worker_started:
        return

    thread = threading.Thread(
        target=_tts_worker,
        daemon=True
    )

    thread.start()

    _worker_started = True


# ─── INTERNAL BLOCKING SPEECH ────────────────────────────────────────────────

def _speak_blocking(
    text: str,
    voice: str = "af_heart",
    speed: float = 1.0,
    emotion: Optional[str] = None
):
    """Actual blocking speech generation."""

    if not text or not text.strip():
        return

    kokoro = _get_kokoro()

    final_speed = _emotion_speed(speed, emotion)

    samples, sample_rate = kokoro.create(
        text,
        voice=voice,
        speed=final_speed,
        lang="en-us"
    )

    sd.play(samples, sample_rate)
    sd.wait()


# ─── PUBLIC SPEAK FUNCTION ───────────────────────────────────────────────────

def speak(
    text: str,
    voice: str = "af_heart",
    speed: float = 1.0,
    emotion: Optional[str] = None
):
    """
    Queues speech without blocking PRIA cognition.
    """

    if not text or not text.strip():
        return

    _start_worker()

    _speech_queue.put({
        "text": text,
        "voice": voice,
        "speed": speed,
        "emotion": emotion,
    })


# ─── WAV BYTE GENERATION FOR API ─────────────────────────────────────────────

def speak_to_bytes(
    text: str,
    voice: str = "af_heart",
    speed: float = 1.0,
    emotion: Optional[str] = None
) -> bytes:
    """
    Generates speech and returns raw WAV bytes.
    Used by api.py.
    """

    if not text or not text.strip():
        return b""

    try:
        kokoro = _get_kokoro()

        final_speed = _emotion_speed(speed, emotion)

        samples, sample_rate = kokoro.create(
            text,
            voice=voice,
            speed=final_speed,
            lang="en-us"
        )

        buf = io.BytesIO()

        sf.write(
            buf,
            samples,
            sample_rate,
            format="WAV"
        )

        buf.seek(0)

        return buf.read()

    except Exception as e:
        print(f"[VOICE] Output error: {e}")
        return b""


# ─── INPUT — WHISPER ─────────────────────────────────────────────────────────

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
    Records audio and transcribes via Whisper.
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

        input()

        sd.stop()

        audio = recording.flatten()

        model = _get_whisper()

        result = model.transcribe(audio, fp16=False)

        text = result.get("text", "").strip()

        return text

    except Exception as e:
        print(f"[VOICE] Input error: {e}")
        return ""