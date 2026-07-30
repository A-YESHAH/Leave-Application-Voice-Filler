"""
Week 3, Day 3-4 — R2: extraction robustness evaluation.
Runs extract() against real transcripts (both clean typed-equivalent and
Whisper-noisy versions) and measures field-level accuracy against
ground-truth labels.
"""
import re
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.extract import extract

CORPUS_DIR = Path(__file__).parent / "corpus"
LABELS_PATH = CORPUS_DIR / "labels.json"
WHISPER_RESULTS_PATH = Path(__file__).parent / "results" / "r1_whisper_comparison_1785269264.json"  
RESULTS_DIR = Path(__file__).parent / "results"

TODAY = "2026-07-28"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def score_fields(expected: dict, actual: dict) -> tuple[int, int, list[str]]:
    correct = 0
    total = 0
    mismatches = []

    for field, expected_value in expected.items():
        total += 1
        actual_value = actual.get(field)

        if isinstance(expected_value, str) and isinstance(actual_value, str):
            exp_words = set(expected_value.lower().split())
            act_words = set(actual_value.lower().split())
            overlap = len(exp_words & act_words) / max(len(exp_words), 1)
            match = overlap >= 0.5 or expected_value.strip().lower() in actual_value.strip().lower() \
                    or actual_value.strip().lower() in expected_value.strip().lower()
        else:
            match = expected_value == actual_value

        if match:
            correct += 1
        else:
            mismatches.append(f"{field}: expected={expected_value!r} got={actual_value!r}")

    return correct, total, mismatches


def run_eval(model_size: str, whisper_results: dict, labels: dict):
    print(f"\n{'='*60}\nR2 EVALUATION — using '{model_size}' Whisper transcripts\n{'='*60}\n")

    clip_type_correct = 0
    clip_type_total = 0
    field_correct_total = 0
    field_total_total = 0
    per_clip_results = []

    transcripts_by_id = {c["clip_id"]: c["transcript"] for c in whisper_results[model_size]}

    for clip_id, label in labels["clips"].items():
        transcript = transcripts_by_id.get(clip_id)
        if transcript is None:
            print(f"[{clip_id}] no transcript found — skipping")
            continue

        expected_type = label["expected_document_type"]
        expected_fields = label.get("expected_fields", {})

        print(f"--- {clip_id} ({expected_type}) ---")

        try:
            if expected_type in ("unknown", "no_intent"):
                from src.extraction.classify import classify
                predicted_type = classify(transcript)
                type_match = predicted_type == expected_type
                clip_type_total += 1
                clip_type_correct += int(type_match)
                status = "✅" if type_match else "❌"
                print(f"{status} type: expected={expected_type} got={predicted_type}")
                per_clip_results.append({
                    "clip_id": clip_id, "type_match": type_match,
                    "field_accuracy": None, "mismatches": []
                })
                continue

            form = extract(transcript, today=TODAY)
            predicted_type = form.document_type
            type_match = predicted_type == expected_type
            clip_type_total += 1
            clip_type_correct += int(type_match)

            status = "✅" if type_match else "❌"
            print(f"{status} type: expected={expected_type} got={predicted_type}")

            if type_match:
                correct, total, mismatches = score_fields(expected_fields, form.model_dump())
                field_correct_total += correct
                field_total_total += total
                acc = correct / total if total else 1.0
                print(f"   field accuracy: {correct}/{total} ({acc:.0%})")
                for m in mismatches:
                    print(f"   ❌ {m}")
                per_clip_results.append({
                    "clip_id": clip_id, "type_match": True,
                    "field_accuracy": acc, "mismatches": mismatches
                })
            else:
                per_clip_results.append({
                    "clip_id": clip_id, "type_match": False,
                    "field_accuracy": None, "mismatches": ["wrong document type — fields not scored"]
                })

        except ValueError as e:
            print(f"❌ extract() raised: {e}")
            clip_type_total += 1
            per_clip_results.append({
                "clip_id": clip_id, "type_match": False,
                "field_accuracy": None, "mismatches": [f"extract() error: {e}"]
            })
        print()

    print(f"\n{'='*60}\nSUMMARY ({model_size})\n{'='*60}")
    print(f"Document-type accuracy: {clip_type_correct}/{clip_type_total} "
          f"({clip_type_correct/clip_type_total:.0%})")
    if field_total_total:
        print(f"Field extraction accuracy (on correctly-typed clips): "
              f"{field_correct_total}/{field_total_total} ({field_correct_total/field_total_total:.0%})")

    output_path = RESULTS_DIR / f"r2_extraction_eval_{model_size}.json"
    output_path.write_text(json.dumps(per_clip_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Detailed results saved to {output_path}")


if __name__ == "__main__":
    labels = load_json(LABELS_PATH)
    whisper_results = load_json(WHISPER_RESULTS_PATH)

    run_eval("small", whisper_results, labels)
    run_eval("medium", whisper_results, labels)