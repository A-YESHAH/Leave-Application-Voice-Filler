from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stt.transcribe import transcribe

folder = Path(r"C:\Users\DELL\Downloads\voice-form-filler\voice-form-filler\eval\corpus")
files = sorted(f for f in folder.iterdir() if f.suffix.lower() == ".mp4")

for i, f in enumerate(files, 1):
    print(f"clip_{i:03d}  ({f.name}):")
    print(transcribe(f))
    print()