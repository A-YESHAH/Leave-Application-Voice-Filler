"""Prompts for the intent classification + field extraction stage."""

SYSTEM_PROMPT = """You are a form-extraction engine for a voice-based document filler used in Pakistan.
Users speak naturally, often mixing Urdu and English (code-switching). Your job is NOT to translate —
it is to extract structured information into JSON.

Rules:
1. Output ONLY valid JSON. No markdown, no commentary, no code fences.
2. Extract meaning, not exact words. Tolerate transcription noise (mis-transcribed words, informal speech).
3. Resolve relative dates (e.g. "Monday", "agle hafte", "parson") against TODAY'S DATE given below.
   Output resolved dates as YYYY-MM-DD.
4. Convert spoken/Urdu numbers to integers (e.g. "teen din" -> 3).
5. If a field is not mentioned or unclear, leave it as null. Do NOT guess or invent values.
6. Translate any Urdu reason into a short, formal English phrase suitable for an official letter.
   The "reason" field must ONLY contain why leave is needed — never include job title,
   designation, or other unrelated details in this field.
7. CRITICAL — NO HALLUCINATION: Many transcripts will NOT be leave requests at all (greetings,
   date statements, self-introductions, test recordings, unrelated speech). If there is no
   explicit request for leave/absence in the transcript, you MUST set start_date, duration_days,
   and reason to null, even if a date or number happens to be mentioned. A date being spoken
   does not mean it is a leave start date. Only fill these fields when the person is clearly
   asking for time off.
8. leave_type must be one of: "casual", "sick", "annual". Infer from reason if not explicitly
   stated (e.g. illness/fever -> "sick"; wedding/personal event -> "casual"). If truly ambiguous
   or reason is unclear, leave it null rather than guessing.
9. recipient_designation defaults to "Manager" only if a recipient_name is given but no title is
   mentioned. If there is no recipient_name at all, leave recipient_designation null too.

TODAY'S DATE: {today}

Output must be a single JSON object matching this shape:
{{
  "document_type": "leave_application_office",
  "applicant_name": "string" or null,
  "applicant_designation": "string" or null,
  "recipient_name": "string" or null,
  "recipient_designation": "string" or null,
  "company_name": "string" or null,
  "leave_type": "casual" or "sick" or "annual" or null,
  "start_date": "YYYY-MM-DD" or null,
  "duration_days": integer or null,
  "reason": "string" or null,
  "department": "string" or null,
  "employee_id": "string" or null,
  "contact_number": "string" or null
}}
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": "I need 3 days leave starting Monday, my sister is getting married",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office",
            "applicant_name": None,
            "applicant_designation": None,
            "recipient_name": None,
            "recipient_designation": None,
            "company_name": None,
            "leave_type": "casual",
            "start_date": "2026-07-20",
            "duration_days": 3,
            "reason": "sister's wedding",
            "department": None,
            "employee_id": None,
            "contact_number": None,
        },
    },
    {
        "input": "Mujhe Monday se teen din ki chutti chahiye kyunke meri sister ki shaadi hai. "
                 "Manager ka naam Ahmed Khan hai.",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office",
            "applicant_name": None,
            "applicant_designation": None,
            "recipient_name": "Ahmed Khan",
            "recipient_designation": "Manager",
            "company_name": None,
            "leave_type": "casual",
            "start_date": "2026-07-20",
            "duration_days": 3,
            "reason": "sister's wedding",
            "department": None,
            "employee_id": None,
            "contact_number": None,
        },
    },
    {
        # deliberately noisy transcript (simulates Whisper mis-transcription)
        "input": "muje parson se do din ki chuti chahye i am not well",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office",
            "applicant_name": None,
            "applicant_designation": None,
            "recipient_name": None,
            "recipient_designation": None,
            "company_name": None,
            "leave_type": "sick",
            "start_date": "2026-07-18",
            "duration_days": 2,
            "reason": "illness",
            "department": None,
            "employee_id": None,
            "contact_number": None,
        },
    },
    {
        # POSITIVE example: Urdu relative-date expression "agle hafte" (next week)
        "input": "Mujhe agle hafte se 2 din ki chutti chahiye, meri tabiyat theek nahi hai",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office",
            "applicant_name": None,
            "applicant_designation": None,
            "recipient_name": None,
            "recipient_designation": None,
            "company_name": None,
            "leave_type": "sick",
            "start_date": "2026-07-23",
            "duration_days": 2,
            "reason": "illness",
            "department": None,
            "employee_id": None,
            "contact_number": None,
        },
    },
    {
        # NEGATIVE example: no leave request at all
        "input": "Hello, today is 15th of June, Wednesday.",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office",
            "applicant_name": None,
            "applicant_designation": None,
            "recipient_name": None,
            "recipient_designation": None,
            "company_name": None,
            "leave_type": None,
            "start_date": None,
            "duration_days": None,
            "reason": None,
            "department": None,
            "employee_id": None,
            "contact_number": None,
        },
    },
    {
        # NEGATIVE example: self-introduction, not a leave request
        "input": "Good morning, I am Ayesha Niazi and my designation is AI Intern.",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office",
            "applicant_name": "Ayesha Niazi",
            "applicant_designation": "AI Intern",
            "recipient_name": None,
            "recipient_designation": None,
            "company_name": None,
            "leave_type": None,
            "start_date": None,
            "duration_days": None,
            "reason": None,
            "department": None,
            "employee_id": None,
            "contact_number": None,
        },
    },
    {
        # FULL example: nearly all fields present, incl. department + employee_id
        "input": "Mujhe Monday se 3 din ki casual leave chahiye, sister ki shaadi hai. Main "
                 "Software Engineer hoon Engineering department mein, employee ID EMP-2041. "
                 "Manager Ahmed Khan hai, company TechSol Pvt Ltd.",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office",
            "applicant_name": None,
            "applicant_designation": "Software Engineer",
            "recipient_name": "Ahmed Khan",
            "recipient_designation": "Manager",
            "company_name": "TechSol Pvt Ltd",
            "leave_type": "casual",
            "start_date": "2026-07-20",
            "duration_days": 3,
            "reason": "sister's wedding",
            "department": "Engineering",
            "employee_id": "EMP-2041",
            "contact_number": None,
        },
    },
]


def build_messages(transcript: str, today: str) -> list[dict]:
    """Assemble the message list: system prompt + few-shot examples + real input."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(today=today)}]

    for ex in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": f"TODAY: {ex['today']}\nTranscript: {ex['input']}"})
        messages.append({"role": "assistant", "content": _to_json_str(ex["output"])})

    messages.append({"role": "user", "content": f"TODAY: {today}\nTranscript: {transcript}"})
    return messages


def _to_json_str(d: dict) -> str:
    import json
    return json.dumps(d)