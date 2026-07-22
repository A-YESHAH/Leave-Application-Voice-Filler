"""
Day 6-7 — R6 experiment: measure how often extraction fails on first
attempt vs after retries, across a batch of test transcripts.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.extract import extract

TEST_TRANSCRIPTS = [
    "Mujhe Monday se teen din ki chutti chahiye, meri sister ki shaadi hai. Manager ka naam Ahmed Khan hai. Company ka naam TechSol hai, casual leave chahiye.",
    "Sir ko application likhni hai, kal main class attend nahi kar sakta, bukhar hai. Main BSCS 7th semester ka student hoon, roll number 21-CS-045.",
    "K-Electric ko complaint likhni hai, hamare area mein 3 din se roz 8 ghantay loadshedding ho rahi hai. Area Gulshan-e-Iqbal Block 6. Consumer number AL-553421.",
    "muje parson se do din ki chuti chahye i am not well",
    "Mujhe agle hafte se 2 din ki chutti chahiye, meri tabiyat theek nahi hai",
]

if __name__ == "__main__":
    total = len(TEST_TRANSCRIPTS)
    succeeded = 0

    for i, text in enumerate(TEST_TRANSCRIPTS, 1):
        print(f"--- Case {i} ---")
        try:
            form = extract(text, today="2026-07-16")
            print(f"Success: {form.document_type}, complete={form.is_complete()}")
            succeeded += 1
        except ValueError as e:
            print(f"Failed: {e}")
        print()

    print(f"Overall success rate: {succeeded}/{total}")