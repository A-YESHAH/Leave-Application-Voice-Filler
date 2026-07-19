# src/stt/transcribe.py
import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from pathlib import Path
from faster_whisper import WhisperModel

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = WhisperModel("medium", device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str | Path, model: str = "medium") -> str:
    """
    Transcribe audio, auto-detecting language (needed for code-switched Urdu/English).
    Whisper sometimes misdetects Urdu speech as Hindi (language='hi') and outputs
    Devanagari script instead of Urdu/Roman script. When that happens, re-run once
    forcing language='ur' to correct it. Pure English or correctly-detected Urdu
    clips pass through on the first try with no override.
    """
    audio_path = Path(audio_path)
    whisper = _get_model()

    segments, info = whisper.transcribe(str(audio_path))  # auto-detect
    text = " ".join(seg.text.strip() for seg in segments)

    if info.language == "hi":
        print(f"[transcribe] detected 'hi' (likely Urdu misclassified) — retrying with language='ur'")
        segments, info = whisper.transcribe(str(audio_path), language="ur")
        text = " ".join(seg.text.strip() for seg in segments)

    print(f"[debug] language={info.language}, duration={info.duration:.1f}s, text_len={len(text)}")
    return text


if __name__ == "__main__":
    import sys
    print(transcribe(sys.argv[1]))