import json
import os
import re
from datetime import date

from src.extraction.llm_backend import chat_json
from src.utils.date_utils import parse_date, WEEKDAYS, WEEKDAY_FUZZY_CUTOFF
import difflib


DEFAULT_MODEL = os.getenv("GROQ_LLM_MODEL")


EDIT_PROMPT = """
The user has an existing form with these current values:

{current_fields}

Today's date is {today}.

The user said:

"{command}"

Determine which field(s) they want to change.

Return ONLY a valid JSON object containing ONLY the fields that should change.

Examples

User:
change my name to Ali

Response:
{{"student_name":"Ali"}}

User:
change the leave to sick leave

Response:
{{"leave_type":"sick"}}

User:
change the date to next Monday

Response:
{{"start_date":"next Monday"}}

User:
change the duration to 5 days

Response:
{{"duration_days":5}}

If nothing should change, return:

{{}}
"""


DATE_FIELDS = {
    "start_date",
}

INT_FIELDS = {
    "duration_days",
}


def _weekday_phrase_from_command(command: str) -> str | None:
    """
    Scans the user's raw command for a (possibly misspelled) weekday
    name and returns a normalized "next <weekday>" phrase.

    This lets us resolve weekday dates ourselves, deterministically,
    instead of trusting the LLM to have done the date math correctly.
    """

    for word in re.findall(r"[a-zA-Z]+", command.lower()):

        if word in WEEKDAYS:
            return f"next {word}"

        close = difflib.get_close_matches(
            word,
            WEEKDAYS.keys(),
            n=1,
            cutoff=WEEKDAY_FUZZY_CUTOFF,
        )

        if close:
            return f"next {close[0]}"

    return None


def apply_edit_command(
    form,
    command: str,
    model: str | None = DEFAULT_MODEL,
    today: str | None = None,
):
    """
    Uses the LLM to understand edit commands such as:

    - change my name to Ali
    - change the leave to sick leave
    - change the date to next monday
    - make it 5 days

    and updates the form.
    """

    today_str = today or date.today().isoformat()

    current_fields = {
        key: value
        for key, value in form.model_dump().items()
        if key not in ("document_type", "missing_fields")
        and value is not None
    }

    prompt = EDIT_PROMPT.format(
        current_fields=json.dumps(current_fields, indent=2),
        today=today_str,
        command=command,
    )

    raw = chat_json(
        [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
    )

    try:
        changes = json.loads(raw)

    except json.JSONDecodeError:
        return form, []

    changed_fields = []

    for field, value in changes.items():

        if not hasattr(form, field):
            continue

        if field in DATE_FIELDS:

            weekday_override = _weekday_phrase_from_command(command)

            parsed = parse_date(
                weekday_override if weekday_override else str(value)
            )

            if parsed is None:
                continue

            value = parsed

        elif field in INT_FIELDS:

            try:
                value = int(value)

            except Exception:
                continue

        setattr(form, field, value)

        changed_fields.append(field)

    form.compute_missing()

    return form, changed_fields