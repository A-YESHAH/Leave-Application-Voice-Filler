# tests/test_retry_mechanism.py
"""
Confirms the retry loop in extract() actually recovers from a bad first
response, rather than just never being exercised (test_retry.py's 5/5
clean run never triggered a retry).
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch
import src.extraction.extract as extract_module

BAD_JSON = "this is not valid json {broken"
GOOD_JSON = '{"document_type": "leave_application_office", "applicant_name": "Test User", "applicant_designation": "Engineer", "recipient_name": "Manager Name", "recipient_designation": "Manager", "company_name": "TestCo", "leave_type": "casual", "start_date": "2026-07-20", "duration_days": 3, "reason": "personal"}'

call_count = {"n": 0}

def fake_call_llm(messages, model):
    call_count["n"] += 1
    if call_count["n"] == 1:
        return BAD_JSON
    return GOOD_JSON

with patch.object(extract_module, "_call_llm", side_effect=fake_call_llm):
    with patch.object(extract_module, "classify", return_value="leave_application_office"):
        result = extract_module.extract("Mujhe 3 din ki chutti chahiye", today="2026-07-16")
        print(f"Calls made: {call_count['n']}")
        print(f"Recovered form: {result.model_dump_json(indent=2)}")
        assert call_count["n"] == 2, "Expected exactly 1 retry"
        print("✅ Retry mechanism confirmed working")