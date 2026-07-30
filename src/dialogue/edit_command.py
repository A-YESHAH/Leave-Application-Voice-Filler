"""
Parse a natural-language edit command (e.g. 'change the date to Tuesday',
'my name is actually Ali not Ahmed') and apply it to an existing form.
Uses a focused LLM call scoped to just the current form's fields,
rather than re-running full extraction from scratch.
"""
import json
import ollama
from datetime import date

EDIT_PROMPT = """The user has an existing form with these current values:
{current_fields}

Today's date is {today}.

The user just said: "{command}"

Determine which field(s) they want to change and to what value. Return ONLY a JSON object
with just the field(s) that should change and their new values — do NOT include unchanged
fields. Resolve any relative dates mentioned against today's date, output as YYYY-MM-DD.

Example: if current fields include "start_date": "2026-07-20" and the user says
"change it to next Wednesday", return: {{"start_date": "2026-07-22"}}

If the command doesn't clearly map to any field in the current form, return: {{}}
"""


def apply_edit_command(form, command: str, model: str = "llama3.2", today: str | None = None):
    """
    Applies a natural-language edit command to the form. Returns the
    updated form and a list of field names that were changed.
    """
    today_str = today or date.today().isoformat()
    current_fields = {
        k: v for k, v in form.model_dump().items()
        if k not in ("document_type", "missing_fields") and v is not None
    }

    prompt = EDIT_PROMPT.format(
        current_fields=json.dumps(current_fields, indent=2),
        today=today_str,
        command=command,
    )

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format="json",
        options={"temperature": 0},
    )

    try:
        changes = json.loads(response["message"]["content"])
    except json.JSONDecodeError:
        return form, []

    changed_fields = []
    for field, new_value in changes.items():
        if hasattr(form, field):
            setattr(form, field, new_value)
            changed_fields.append(field)

    form.compute_missing()
    return form, changed_fields