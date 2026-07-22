"""Per-document-type extraction prompts. Each type has its own system prompt + few-shot examples,
since required fields differ per form."""

OFFICE_LEAVE_PROMPT = """You are extracting fields for an OFFICE LEAVE APPLICATION from a voice transcript.
Users mix Urdu/English. Extract meaning, not exact words. Tolerate transcription noise.

Rules:
1. Output ONLY valid JSON, no markdown/commentary.
2. Resolve relative dates ("Monday", "agle hafte", "parson") against TODAY'S DATE below -> YYYY-MM-DD.
3. Convert spoken/Urdu numbers to integers ("teen din" -> 3).
4. If a field is not mentioned or unclear, leave it null. Do NOT guess or invent values.
5. "reason" must ONLY contain why leave is needed — never job title or unrelated details.
6. leave_type must be "casual", "sick", or "annual" — infer from reason if not explicit
   (illness -> sick, event/personal -> casual). Leave null if truly ambiguous.
7. recipient_designation defaults to "Manager" only if recipient_name is given but no title stated.
8. Always output applicant/student names in Roman script (English letters), even if the
   transcript gives the name in Urdu script. Transliterate phonetically — do not translate
   the meaning of the name, just its sound (e.g. "عائشہ نیازی" -> "Ayesha Niazi").
9. Common Urdu kinship terms and their correct English translations — use these exactly,
   do not substitute a different family member:
   ami/ammi = mother, abbu/walid = father, behen/bhen = sister, bhai = brother,
   dada/dadi = paternal grandfather/grandmother, nana/nani = maternal grandfather/grandmother,
   khala = maternal aunt, phupo = paternal aunt, chacha/mamu = uncle.

TODAY'S DATE: {today}

Output shape:
{{"document_type": "leave_application_office", "applicant_name": str|null, "applicant_designation": str|null,
"recipient_name": str|null, "recipient_designation": str|null, "company_name": str|null,
"leave_type": str|null, "start_date": str|null, "duration_days": int|null, "reason": str|null,
"department": str|null, "employee_id": str|null, "contact_number": str|null}}
"""

OFFICE_LEAVE_EXAMPLES = [
    {
        "input": "I need 3 days leave starting Monday, my sister is getting married",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office", "applicant_name": None,
            "applicant_designation": None, "recipient_name": None, "recipient_designation": None,
            "company_name": None, "leave_type": "casual", "start_date": "2026-07-20",
            "duration_days": 3, "reason": "sister's wedding", "department": None,
            "employee_id": None, "contact_number": None,
        },
    },
    {
        "input": "Mujhe Monday se teen din ki chutti chahiye kyunke meri sister ki shaadi hai. Manager ka naam Ahmed Khan hai.",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office", "applicant_name": None,
            "applicant_designation": None, "recipient_name": "Ahmed Khan",
            "recipient_designation": "Manager", "company_name": None, "leave_type": "casual",
            "start_date": "2026-07-20", "duration_days": 3, "reason": "sister's wedding",
            "department": None, "employee_id": None, "contact_number": None,
        },
    },
    {
        "input": "muje parson se do din ki chuti chahye i am not well",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office", "applicant_name": None,
            "applicant_designation": None, "recipient_name": None, "recipient_designation": None,
            "company_name": None, "leave_type": "sick", "start_date": "2026-07-18",
            "duration_days": 2, "reason": "illness", "department": None,
            "employee_id": None, "contact_number": None,
        },
    },
    {
        "input": "Mujhe agle hafte se 2 din ki chutti chahiye, meri tabiyat theek nahi hai",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office", "applicant_name": None,
            "applicant_designation": None, "recipient_name": None, "recipient_designation": None,
            "company_name": None, "leave_type": "sick", "start_date": "2026-07-23",
            "duration_days": 2, "reason": "illness", "department": None,
            "employee_id": None, "contact_number": None,
        },
    },
    {
        "input": "Hello, today is 15th of June, Wednesday.",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office", "applicant_name": None,
            "applicant_designation": None, "recipient_name": None, "recipient_designation": None,
            "company_name": None, "leave_type": None, "start_date": None,
            "duration_days": None, "reason": None, "department": None,
            "employee_id": None, "contact_number": None,
        },
    },
    {
        "input": "Good morning, I am Ayesha Niazi and my designation is AI Intern.",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office", "applicant_name": "Ayesha Niazi",
            "applicant_designation": "AI Intern", "recipient_name": None,
            "recipient_designation": None, "company_name": None, "leave_type": None,
            "start_date": None, "duration_days": None, "reason": None,
            "department": None, "employee_id": None, "contact_number": None,
        },
    },
    {
        "input": "Mujhe Monday se 3 din ki casual leave chahiye, sister ki shaadi hai. Main "
                 "Software Engineer hoon Engineering department mein, employee ID EMP-2041. "
                 "Manager Ahmed Khan hai, company TechSol Pvt Ltd.",
        "today": "2026-07-16",
        "output": {
            "document_type": "leave_application_office", "applicant_name": None,
            "applicant_designation": "Software Engineer", "recipient_name": "Ahmed Khan",
            "recipient_designation": "Manager", "company_name": "TechSol Pvt Ltd",
            "leave_type": "casual", "start_date": "2026-07-20", "duration_days": 3,
            "reason": "sister's wedding", "department": "Engineering",
            "employee_id": "EMP-2041", "contact_number": None,
        },
    },
]

UNIVERSITY_LEAVE_PROMPT = """You are extracting fields for a UNIVERSITY/SCHOOL LEAVE APPLICATION
from a voice transcript. Users mix Urdu/English.

Rules:
1. Output ONLY valid JSON, no markdown/commentary.
2. Resolve relative dates against TODAY'S DATE below -> YYYY-MM-DD.
   IMPORTANT: "kal" means both "yesterday" and "tomorrow" in Urdu. Since this is a future leave
   request, resolve "kal" as TOMORROW relative to today.
3. Convert spoken/Urdu numbers to integers.
4. If a field is not mentioned, leave it null. Do NOT guess.
5. "Sir"/"Madam" in the utterance sets recipient_salutation accordingly.
7. Always output applicant/student names in Roman script (English letters), even if the
   transcript gives the name in Urdu script. Transliterate phonetically — do not translate
   the meaning of the name, just its sound (e.g. "عائشہ نیازی" -> "Ayesha Niazi").
   6. Common Urdu kinship terms and their correct English translations — use these exactly,
   do not substitute a different family member:
   ami/ammi = mother, abbu/walid = father, behen/bhen = sister, bhai = brother,
   dada/dadi = paternal grandfather/grandmother, nana/nani = maternal grandfather/grandmother,
   khala = maternal aunt, phupo = paternal aunt, chacha/mamu = uncle.

TODAY'S DATE: {today}

Output shape:
{{"document_type": "leave_application_university", "student_name": str|null, "roll_number": str|null,
"program": str|null, "institution_name": str|null, "start_date": str|null, "duration_days": int|null,
"reason": str|null, "semester": str|null, "department": str|null,
"recipient_designation": str|null, "recipient_salutation": str|null}}
"""

UNIVERSITY_LEAVE_EXAMPLES = [
    {
        "input": "Sir ko application likhni hai, kal main class attend nahi kar sakta, bukhar hai. Main BSCS 7th semester ka student hoon, roll number 21-CS-045.",
        "today": "2026-07-15",
        "output": {
            "document_type": "leave_application_university", "student_name": None,
            "roll_number": "21-CS-045", "program": "BSCS", "institution_name": None,
            "start_date": "2026-07-16", "duration_days": 1, "reason": "fever",
            "semester": "7", "department": None, "recipient_designation": "Class Teacher",
            "recipient_salutation": "Sir",
        },
    },
]

COMPLAINT_LETTER_PROMPT = """You are extracting fields for a COMPLAINT LETTER (utility/service)
from a voice transcript. Users mix Urdu/English.

Rules:
1. Output ONLY valid JSON, no markdown/commentary.
2. Resolve relative time expressions against TODAY'S DATE below -> YYYY-MM-DD, where possible.
3. Convert spoken/Urdu numbers to integers/text as appropriate.
4. If a field is not mentioned, leave it null. Do NOT guess.
5. complaint_subject: write a concise formal phrase summarizing the issue
   (e.g. "Prolonged Unscheduled Load Shedding"), even though the user won't say this exact phrase.
6. issue_description: the factual detail of the complaint (what's happening, how long, how often).
7. Always output applicant/student names in Roman script (English letters), even if the
   transcript gives the name in Urdu script. Transliterate phonetically — do not translate
   the meaning of the name, just its sound (e.g. "عائشہ نیازی" -> "Ayesha Niazi").
   6. Common Urdu kinship terms and their correct English translations — use these exactly,
   do not substitute a different family member:
   ami/ammi = mother, abbu/walid = father, behen/bhen = sister, bhai = brother,
   dada/dadi = paternal grandfather/grandmother, nana/nani = maternal grandfather/grandmother,
   khala = maternal aunt, phupo = paternal aunt, chacha/mamu = uncle.

TODAY'S DATE: {today}

Output shape:
{{"document_type": "complaint_letter", "complainant_name": str|null, "address": str|null,
"contact_number": str|null, "organization_name": str|null, "complaint_subject": str|null,
"issue_description": str|null, "reference_number": str|null, "recipient_designation": str|null,
"organization_address": str|null, "issue_start": str|null}}
"""

COMPLAINT_LETTER_EXAMPLES = [
    {
        "input": "K-Electric ko complaint likhni hai, hamare area mein 3 din se roz 8 ghantay loadshedding ho rahi hai. Area Gulshan-e-Iqbal Block 6. Consumer number AL-553421.",
        "today": "2026-07-15",
        "output": {
            "document_type": "complaint_letter", "complainant_name": None,
            "address": "Gulshan-e-Iqbal Block 6", "contact_number": None,
            "organization_name": "K-Electric",
            "complaint_subject": "Prolonged Unscheduled Load Shedding",
            "issue_description": "8 hours daily loadshedding for the past 3 days",
            "reference_number": "AL-553421", "recipient_designation": "Customer Services Manager",
            "organization_address": None, "issue_start": "2026-07-12",
        },
    },
]

EXTRACTION_PROMPTS = {
    "leave_application_office": (OFFICE_LEAVE_PROMPT, OFFICE_LEAVE_EXAMPLES),
    "leave_application_university": (UNIVERSITY_LEAVE_PROMPT, UNIVERSITY_LEAVE_EXAMPLES),
    "complaint_letter": (COMPLAINT_LETTER_PROMPT, COMPLAINT_LETTER_EXAMPLES),
}


def build_messages(document_type: str, transcript: str, today: str) -> list[dict]:
    system_template, examples = EXTRACTION_PROMPTS[document_type]
    messages = [{"role": "system", "content": system_template.format(today=today)}]
    for ex in examples:
        messages.append({"role": "user", "content": f"TODAY: {ex['today']}\nTranscript: {ex['input']}"})
        messages.append({"role": "assistant", "content": _to_json_str(ex["output"])})
    messages.append({"role": "user", "content": f"TODAY: {today}\nTranscript: {transcript}"})
    return messages


def _to_json_str(d: dict) -> str:
    import json
    return json.dumps(d)