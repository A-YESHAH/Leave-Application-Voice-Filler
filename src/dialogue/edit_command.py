import json
import os
from datetime import date

from src.extraction.llm_backend import chat_json
from src.utils.date_utils import parse_date

DEFAULT_MODEL = os.getenv("GROQ_LLM_MODEL")

EDIT_PROMPT = """
The user has an existing form with these current values:
{current_fields}

Today's date is {today}.

The user just said:

"{command}"

Determine which field(s) they want to change and to what value.

Return ONLY a valid JSON object containing ONLY the fields that should change.

Examples:

User: change my name to Ali
Response:
{{"student_name":"Ali"}}

User: change the leave to sick leave
Response:
{{"leave_type":"sick"}}

User: change the date to next Monday
Response:
{{"start_date":"next Monday"}}

User: change the date to 26 August 2026
Response:
{{"start_date":"26 August 2026"}}

User: change the duration to 5 days
Response:
{{"duration_days":5}}

If nothing should change, return:
{{}}
"""

DATE_FIELDS = {"start_date"}
INT_FIELDS = {"duration_days"}


def apply_edit_command(
    form,
    command: str,
    model: str | None = DEFAULT_MODEL,
    today: str | None = None,
):
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
        [{"role": "user", "content": prompt}],
        model=model,
    )

    try:
        changes = json.loads(raw)
    except json.JSONDecodeError:
        return form, []

    changed_fields = []

    for field, value in changes.items():

        if field in DATE_FIELDS and isinstance(value, str):
            parsed = parse_date(value)
            if parsed:
                value = parsed

        # Convert integers
        if field in INT_FIELDS:
            try:
                value = int(value)
            except (ValueError, TypeError):
                pass

        if hasattr(form, field):
            setattr(form, field, value)
            changed_fields.append(field)

    form.compute_missing()

    return form, changed_fields