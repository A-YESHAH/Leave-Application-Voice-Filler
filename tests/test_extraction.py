from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.extract import extract
from src.stt.transcribe import transcribe

TODAY = "2026-07-16"

TYPED_TEST_CASES = [
    "I need 3 days leave starting Monday, my sister is getting married",
    "Mujhe agle hafte se 2 din ki chutti chahiye, meri tabiyat theek nahi hai",
    "I want to apply for leave next Wednesday for one day, doctor's appointment",
    "chutti chahiye parson se, family emergency hai",  # deliberately vague, no duration
]

SAMPLE_DIR = Path(__file__).parent.parent / "data" / "sample_audio"


def run_typed():
    print("=== TYPED TEXT TESTS ===")
    for i, text in enumerate(TYPED_TEST_CASES, 1):
        print(f"\n--- Case {i} ---")
        print(f"Input: {text}")
        result = extract(text, today=TODAY)
        print(result.model_dump_json(indent=2))
        print(f"Complete: {result.is_complete()}  Missing: {result.missing_fields}")


def run_on_transcripts():
    print("\n=== TRANSCRIBED AUDIO TESTS ===")
    exts = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".ogg"}
    audio_files = sorted(f for f in SAMPLE_DIR.iterdir() if f.suffix.lower() in exts)

    if not audio_files:
        print(f"No audio files found in {SAMPLE_DIR}")
        return

    for f in audio_files[:5]:
        print(f"\n--- {f.name} ---")
        transcript = transcribe(f)
        print(f"Transcript: {transcript}")
        result = extract(transcript, today=TODAY)
        print(result.model_dump_json(indent=2))
        print(f"Complete: {result.is_complete()}  Missing: {result.missing_fields}")


if __name__ == "__main__":
    run_typed()
    run_on_transcripts()