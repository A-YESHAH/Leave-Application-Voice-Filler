import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from pathlib import Path

STT_BACKEND = os.getenv("STT_BACKEND", "local")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "medium")

_model = None

if STT_BACKEND == "groq":
    from groq import Groq
    _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
else:
    from faster_whisper import WhisperModel


def _get_model():
    global _model
    if _model is None:
        _model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str | Path, model: str = None) -> str:
    """
    Transcribe audio, auto-detecting language (needed for code-switched
    Urdu/English). Whisper sometimes misdetects Urdu speech as Hindi
    (language='hi') and outputs Devanagari script instead of Urdu/Roman
    script. When that happens, re-run once forcing language='ur'.
    """
    audio_path = Path(audio_path)

    if STT_BACKEND == "groq":
        with open(audio_path, "rb") as f:
            result = _groq_client.audio.transcriptions.create(
                file=(str(audio_path), f.read()),
                model="whisper-large-v3",
            )
        text = result.text
        print(f"[debug] backend=groq, text_len={len(text)}")
        return text

    whisper = _get_model()
    segments, info = whisper.transcribe(str(audio_path))
    text = " ".join(seg.text.strip() for seg in segments)

    if info.language == "hi":
        print(f"[transcribe] detected 'hi' (likely Urdu misclassified) — retrying with language='ur'")
        segments, info = whisper.transcribe(str(audio_path), language="ur")
        text = " ".join(seg.text.strip() for seg in segments)

    print(f"[debug] backend=local, model={WHISPER_MODEL_SIZE}, language={info.language}, "
          f"duration={info.duration:.1f}s, text_len={len(text)}")
    return text


if __name__ == "__main__":
    import sys
    print(transcribe(sys.argv[1]))