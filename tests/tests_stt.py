"""
Manual test: transcribe 5 English recordings, print results for eyeballing.
Put 5 sample .wav/.mp3 files in data/sample_audio/ first.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stt.transcribe import transcribe

SAMPLE_DIR = Path(__file__).parent.parent / "data" / "sample_audio"

def main():
    exts = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".ogg"}
    audio_files = sorted(f for f in SAMPLE_DIR.iterdir() if f.suffix.lower() in exts)
    if not audio_files:
        print(f"No audio files found in {SAMPLE_DIR}")
        return

    for f in audio_files[:5]:
        print(f"--- {f.name} ---")
        text = transcribe(f)
        print(text)
        print()

if __name__ == "__main__":
    main()