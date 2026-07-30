"""
eval/run_r1_whisper_comparison.py
R1: compare Whisper model sizes on the labeled corpus — accuracy vs latency vs cost.
"""
import json
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from faster_whisper import WhisperModel

CORPUS_DIR = Path(__file__).parent / "corpus"
CLIPS_DIR = CORPUS_DIR / "clips"
LABELS_PATH = CORPUS_DIR / "labels.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

MODEL_SIZES = ["small", "medium"]  # add "large-v3" if your machine can handle it


def load_labels() -> dict:
    if not LABELS_PATH.exists():
        print(f"No labels.json found at {LABELS_PATH} — create it first.")
        return {}
    return json.loads(LABELS_PATH.read_text(encoding="utf-8"))


def transcribe_with_model(model_size: str, audio_path: Path) -> tuple[str, float, str]:
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    start = time.time()
    segments, info = model.transcribe(str(audio_path))
    text = " ".join(seg.text.strip() for seg in segments)
    if info.language == "hi":
        segments, info = model.transcribe(str(audio_path), language="ur")
        text = " ".join(seg.text.strip() for seg in segments)
    elapsed = time.time() - start
    return text, elapsed, info.language


def run_comparison():
    data = load_labels()
    if not data:
        return

    labels = data.get("clips", {})

    if not labels:
        print("No clip labels found in labels.json")
        return

    results = {size: [] for size in MODEL_SIZES}

    for clip_id, label_data in labels.items():
        audio_path = CLIPS_DIR / f"{clip_id}.mp4"
        if not audio_path.exists():
            print(f"Skipping {clip_id} — audio file not found at {audio_path}")
            continue

        print(f"\n=== {clip_id} ===")
        print(f"Expected gist: {label_data.get('expected_transcript_gist')}")

        for model_size in MODEL_SIZES:
            text, elapsed, detected_lang = transcribe_with_model(model_size, audio_path)
            print(f"  [{model_size}] ({elapsed:.1f}s, lang={detected_lang}): {text}")
            results[model_size].append({
                "clip_id": clip_id,
                "transcript": text,
                "latency_sec": round(elapsed, 2),
                "detected_language": detected_lang,
                "expected_gist": label_data.get("expected_transcript_gist"),
            })

    output_path = RESULTS_DIR / f"r1_whisper_comparison_{int(time.time())}.json"
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults saved to {output_path}")
    print("\nManually review each transcript against expected_gist and score "
          "'preserves all key facts: yes/no' per clip, per model size, to compute "
          "the R1 accuracy-vs-latency table.")


if __name__ == "__main__":
    run_comparison()