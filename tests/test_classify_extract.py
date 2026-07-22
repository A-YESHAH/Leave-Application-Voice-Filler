"""
Week 2 Day 1-2: test classify() + extract() across all 3 document types.
Run on typed text first (clean signal on classifier + prompt quality),
then on real transcripts.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.classify import classify
from src.extraction.extract import extract
from src.stt.transcribe import transcribe

TODAY = "2026-07-16"

TEST_CASES = [

    ("leave_application_office",
     "Mujhe Monday se teen din ki chutti chahiye, meri sister ki shaadi hai. "
     "Manager ka naam Ahmed Khan hai. Company ka naam TechSol hai, casual leave chahiye."),

    ("leave_application_university",
     "Sir ko application likhni hai, kal main class attend nahi kar sakta, bukhar hai. "
     "Main BSCS 7th semester ka student hoon, roll number 21-CS-045."),

    ("complaint_letter",
     "K-Electric ko complaint likhni hai, hamare area mein 3 din se roz 8 ghantay "
     "loadshedding ho rahi hai. Area Gulshan-e-Iqbal Block 6. Consumer number AL-553421."),

    ("unknown",
     "Hello, today is 15th of June, Wednesday."),  
]

SAMPLE_DIR = Path(__file__).parent.parent / "data" / "sample_audio"


def run_typed():
    print("=== CLASSIFIER + EXTRACTION — TYPED TEXT ===\n")
    correct = 0
    for expected_type, text in TEST_CASES:
        print(f"--- Input: {text[:60]}... ---")
        predicted = classify(text)
        match = "✅" if predicted == expected_type else "❌"
        print(f"Expected: {expected_type} | Got: {predicted} {match}")
        if predicted == expected_type:
            correct += 1

        if predicted != "unknown" and predicted in {"leave_application_office",
                                                       "leave_application_university",
                                                       "complaint_letter"}:
            try:
                form = extract(text, today=TODAY)
                print(form.model_dump_json(indent=2))
                print(f"Complete: {form.is_complete()}  Missing: {form.missing_fields}")
            except ValueError as e:
                print(f"extract() raised: {e}")
        print()

    print(f"Classifier accuracy: {correct}/{len(TEST_CASES)}\n")


def run_on_transcripts():
    print("=== CLASSIFIER + EXTRACTION — REAL AUDIO ===\n")
    exts = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".ogg"}
    audio_files = sorted(f for f in SAMPLE_DIR.iterdir() if f.suffix.lower() in exts)

    if not audio_files:
        print(f"No audio files found in {SAMPLE_DIR}")
        return

    for f in audio_files:
        print(f"--- {f.name} ---")
        transcript = transcribe(f)
        print(f"Transcript: {transcript}")

        predicted = classify(transcript)
        print(f"Classified as: {predicted}")

        if predicted != "unknown" and predicted in {"leave_application_office",
                                                       "leave_application_university",
                                                       "complaint_letter"}:
            try:
                form = extract(transcript, today=TODAY)
                print(form.model_dump_json(indent=2))
                print(f"Complete: {form.is_complete()}  Missing: {form.missing_fields}")
            except ValueError as e:
                print(f"extract() raised: {e}")
        print()


if __name__ == "__main__":
    run_typed()
    run_on_transcripts()