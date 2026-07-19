# quick manual test — tests/test_generate_pipeline.py
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stt.transcribe import transcribe
from src.extraction.extract import extract
from src.generation.generate import generate

AUDIO_FILE = Path(__file__).parent.parent / "data" / "sample_audio" / "3.mp4"  # pick your fullest clip

transcript = transcribe(AUDIO_FILE)
print(f"Transcript: {transcript}")

form = extract(transcript, today="2026-07-16")
print(form.model_dump_json(indent=2))

if form.is_complete():
    out = generate(form, "test_pipeline_output.docx")
    print(f"Generated: {out}")
else:
    print(f"Incomplete — missing: {form.missing_fields}. Can't generate yet (this is expected — "
          f"clarification loop for these comes in Week 2).")