from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from src.extraction.normalize import (
    extract_number_word, resolve_relative_date, cross_check_duration
)

TODAY = date(2026, 7, 16)

NUMBER_CASES = [
    ("teen din ki chutti", 3),
    ("do din chahiye", 2),
    ("5 days leave", 5),
    ("paanch din", 5),
    ("chutti chahiye", None),
    ("roll number 21-CS-045", None),
    ("employee ID EMP-2041, 3 din chutti", 3),
]

DATE_CASES = [
    ("Monday se leave", "2026-07-20"),
    ("kal se chutti", "2026-07-17"),
    ("parson se", "2026-07-18"),
    ("agle hafte se", "2026-07-23"),
    ("aaj se", "2026-07-16"),
    ("next Wednesday", "2026-07-22"),
    ("chutti chahiye", None),
]


def run_number_tests():
    print("=== Number word extraction ===")
    correct = 0
    for text, expected in NUMBER_CASES:
        result = extract_number_word(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' -> {result} (expected {expected})")
        if result == expected:
            correct += 1
    print(f"Accuracy: {correct}/{len(NUMBER_CASES)}\n")


def run_date_tests():
    print("=== Relative date resolution ===")
    correct = 0
    for text, expected in DATE_CASES:
        result = resolve_relative_date(text, TODAY)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' -> {result} (expected {expected})")
        if result == expected:
            correct += 1
    print(f"Accuracy: {correct}/{len(DATE_CASES)}\n")


def run_cross_check_tests():
    print("=== Duration cross-check (LLM value vs rule-based) ===")
    cases = [
        ("teen din ki chutti", 3, (3, False)),
        ("teen din ki chutti", None, (3, True)),
        ("teen din ki chutti", 5, (3, True)),
        ("chutti chahiye", None, (None, False)),
        ("roll number 21-CS-045", 1, (1, False)),
    ]
    for transcript, llm_value, expected in cases:
        result = cross_check_duration(transcript, llm_value)
        status = "✅" if result == expected else "❌"
        print(f"{status} transcript='{transcript}' llm={llm_value} -> {result} (expected {expected})")


if __name__ == "__main__":
    run_number_tests()
    run_date_tests()
    run_cross_check_tests()