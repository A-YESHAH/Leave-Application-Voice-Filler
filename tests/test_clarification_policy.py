"""
Week 3, Day 5 — R4: test the confirm-vs-ask-vs-assume policy on
ambiguous leave_type cases. Forces office document type directly,
since these test transcripts are deliberately short/bare and would
otherwise correctly trigger the unknown-classifier fallback (by
design, per Week 3's classifier fixes) — that's a separate concern
from what this test is checking.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.extract import extract
from src.dialogue.clarify import needs_confirmation, apply_confirmation

AMBIGUOUS_CASES = [
    "Mujhe teen din ki chutti chahiye, meri tabiyat theek nahi",
    "Mujhe do din ki chutti chahiye, cousin ki shaadi hai",
    "Mujhe chutti chahiye",
]

for text in AMBIGUOUS_CASES:
    print(f"--- {text} ---")
    form = extract(text, today="2026-07-28", forced_doc_type="leave_application_office")
    print(f"Inferred leave_type: {form.leave_type}")
    confirmed = set()
    result = needs_confirmation(form, confirmed)
    if result:
        field, question = result
        print(f"Confirmation triggered: {question}")
    else:
        print("No confirmation needed (leave_type not inferred)")
    print()