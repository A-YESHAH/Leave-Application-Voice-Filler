from typing import Any

QUESTIONS: dict[str, dict[str, str]] = {
    "leave_application_office": {
        "applicant_name": "What is your full name?",
        "applicant_designation": "What is your job title/designation?",
        "recipient_name": "Who is this addressed to (your manager's name)?",
        "recipient_designation": "What is their designation/title (e.g. Manager, HR Manager)?",
        "company_name": "What is your company's name?",
        "leave_type": "What type of leave is this — casual, sick, or annual?",
        "start_date": "What date does your leave start? (e.g. 2026-07-20)",
        "duration_days": "How many days of leave do you need?",
        "reason": "What is the reason for your leave?",
    },
    "leave_application_university": {
        "student_name": "What is your full name?",
        "roll_number": "What is your roll number?",
        "program": "What program are you enrolled in? (e.g. BSCS)",
        "institution_name": "What is the name of your institution?",
        "start_date": "What date does your leave start? (e.g. 2026-07-20)",
        "duration_days": "How many days of leave do you need?",
        "reason": "What is the reason for your leave?",
        "recipient_designation": "Who is this addressed to (e.g. Class Teacher, Head of Department)?",
        "recipient_salutation": "How should they be addressed — Sir or Madam?",
        "semester": "What semester are you currently in?",
        "department": "What department is this program under?",
    },
    "complaint_letter": {
        "complainant_name": "What is your full name?",
        "address": "What is your address / area?",
        "contact_number": "What is a contact number we can reach you on?",
        "organization_name": "Which organization is this complaint addressed to?",
        "recipient_designation": "Who is this addressed to (e.g. Customer Services Manager)?",
        "complaint_subject": "In a few words, what is this complaint about?",
        "issue_description": "Please describe the issue in more detail (what's happening, since when).",
    },
}

INT_FIELDS = {"duration_days"}


def get_next_question(form) -> tuple[str, str] | None:
    form.compute_missing()
    if not form.missing_fields:
        return None

    doc_type = form.document_type
    field = form.missing_fields[0]
    question = QUESTIONS.get(doc_type, {}).get(field, f"Please provide: {field.replace('_', ' ')}")
    return field, question


def apply_answer(form, field: str, raw_answer: str):
    raw_answer = raw_answer.strip()

    if field in INT_FIELDS:
        try:
            value: Any = int(raw_answer)
        except ValueError:
            value = raw_answer
    else:
        value = raw_answer

    setattr(form, field, value)
    form.compute_missing()
    return form