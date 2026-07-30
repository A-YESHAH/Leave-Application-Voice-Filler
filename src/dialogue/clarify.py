from typing import Any
import dateparser
from datetime import datetime


QUESTIONS: dict[str, dict[str, str]] = {
    "leave_application_office": {
        "applicant_name": "What is your full name?",
        "applicant_designation": "What is your job title/designation?",
        "recipient_name": "Who is this addressed to (your manager's name)?",
        "recipient_designation": "What is their designation/title (e.g. Manager, HR Manager)?",
        "company_name": "What is your company's name?",
        "leave_type": "What type of leave is this — casual, sick, or annual?",
        "start_date": "When does your leave start? (e.g. tomorrow, next Monday, 26 August 2026)",
        "duration_days": "How many days of leave do you need?",
        "reason": "What is the reason for your leave?",
    },
    "leave_application_university": {
        "student_name": "What is your full name?",
        "roll_number": "What is your roll number?",
        "program": "What program are you enrolled in? (e.g. BSCS)",
        "institution_name": "What is the name of your institution?",
        "start_date": "When does your leave start? (e.g. tomorrow, next Monday, 26 August 2026)",
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

CONFIRMATION_FIELDS = {
    "leave_application_office": ["leave_type"],
}

CONFIRMATION_PROMPTS = {
    "leave_type": lambda form: (
        f"Based on your reason ('{form.reason}'), I'm assuming this is "
        f"**{form.leave_type} leave**. Is that correct? "
        f"(yes / or tell me the correct type)"
    ),
}

INT_FIELDS = {"duration_days"}
DATE_FIELDS = {"start_date"}


def get_next_question(form) -> tuple[str, str] | None:
    form.compute_missing()
    print(form.model_dump())

    if not form.missing_fields:
        return None

    doc_type = form.document_type
    field = form.missing_fields[0]

    question = QUESTIONS.get(doc_type, {}).get(
        field,
        f"Please provide: {field.replace('_', ' ')}",
    )

    return field, question


def parse_date(text: str) -> str | None:
    if not text:
        return None

    settings = {
        "PREFER_DATES_FROM": "future",
        "DATE_ORDER": "DMY",
    }

    parsed = dateparser.parse(text, settings=settings)

    if parsed:
        return parsed.date().isoformat()

    # Try common formats manually
    for fmt in (
        "%d %B %Y",
        "%d %b %Y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass

    return None


def apply_answer(form, field: str, raw_answer: str):
    raw_answer = raw_answer.strip()

    if field in INT_FIELDS:
        try:
            value: Any = int(raw_answer)
        except ValueError:
            value = raw_answer

    elif field in DATE_FIELDS:
        parsed = parse_date(raw_answer)

        if parsed:
            value = parsed
        else:
            value = raw_answer

    else:
        value = raw_answer

    setattr(form, field, value)
    form.compute_missing()

    return form


def needs_confirmation(form, already_confirmed: set[str]) -> tuple[str, str] | None:
    doc_type = form.document_type
    fields_to_confirm = CONFIRMATION_FIELDS.get(doc_type, [])

    for field in fields_to_confirm:
        value = getattr(form, field, None)

        if value is not None and field not in already_confirmed:
            prompt_fn = CONFIRMATION_PROMPTS.get(field)

            if prompt_fn:
                return field, prompt_fn(form)

    return None


def apply_confirmation(form, field: str, user_response: str, already_confirmed: set[str]):
    response_lower = user_response.strip().lower()

    affirmative = {
        "yes",
        "yeah",
        "yep",
        "correct",
        "haan",
        "ہاں",
        "ٹھیک",
    }

    if response_lower not in affirmative:
        if field == "leave_type":
            for candidate in ("casual", "sick", "annual"):
                if candidate in response_lower:
                    setattr(form, field, candidate)
                    break

    already_confirmed.add(field)
    return form