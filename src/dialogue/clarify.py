from typing import Any

from src.utils.date_utils import parse_date


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
    "leave_application_office": [
        "leave_type",
    ],
}


CONFIRMATION_PROMPTS = {
    "leave_type": lambda form: (
        f"Based on your reason ('{form.reason}'), "
        f"I'm assuming this is **{form.leave_type} leave**. "
        f"Is that correct? (yes / or tell me the correct type)"
    )
}


INT_FIELDS = {
    "duration_days",
}

DATE_FIELDS = {
    "start_date",
}


def get_next_question(form) -> tuple[str, str] | None:
    """
    Returns the next missing field and its question.
    """

    form.compute_missing()

    if not form.missing_fields:
        return None

    field = form.missing_fields[0]

    question = QUESTIONS.get(
        form.document_type,
        {},
    ).get(
        field,
        f"Please provide {field.replace('_', ' ')}",
    )

    return field, question


def apply_answer(
    form,
    field: str,
    raw_answer: str,
):
    """
    Applies a user's clarification answer.
    """

    raw_answer = raw_answer.strip()

    if field in INT_FIELDS:

        try:
            value: Any = int(raw_answer)

        except ValueError:
            value = None

    elif field in DATE_FIELDS:

        parsed = parse_date(raw_answer)

        if parsed:
            value = parsed
        else:
            value = None

    else:

        value = raw_answer

    setattr(form, field, value)

    form.compute_missing()

    return form


def needs_confirmation(
    form,
    already_confirmed: set[str],
):
    """
    Determines whether a confirmation question should be asked.
    """

    fields = CONFIRMATION_FIELDS.get(
        form.document_type,
        [],
    )

    for field in fields:

        value = getattr(form, field, None)

        if value is None:
            continue

        if field in already_confirmed:
            continue

        prompt_fn = CONFIRMATION_PROMPTS.get(field)

        if prompt_fn:
            return field, prompt_fn(form)

    return None


def apply_confirmation(
    form,
    field: str,
    user_response: str,
    already_confirmed: set[str],
):
    """
    Applies confirmation response.
    """

    response = user_response.strip().lower()

    affirmative = {
        "yes",
        "yeah",
        "yep",
        "correct",
        "right",
        "haan",
        "ہاں",
        "ji",
        "جی",
        "ok",
        "okay",
    }

    if response not in affirmative:

        if field == "leave_type":

            for leave in (
                "casual",
                "sick",
                "annual",
            ):

                if leave in response:
                    setattr(form, field, leave)
                    break

    already_confirmed.add(field)

    form.compute_missing()

    return form