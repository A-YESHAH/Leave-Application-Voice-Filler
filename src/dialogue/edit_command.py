"""
Parse a natural-language edit command (e.g. "change the date to Tuesday",
"my name is actually Ali not Ahmed") and apply it to an existing form.

Uses the configured LLM backend (Groq or Ollama via llm_backend.py)
to determine which fields should be updated.
"""

import json
from datetime import date

from src.extraction.llm_backend import chat_json

EDIT_PROMPT = """
You are an assistant that edits structured forms.

IMPORTANT:
- Respond ONLY with valid JSON.
- Return ONLY a JSON object.
- Do NOT use markdown.
- Do NOT explain your answer.
- If nothing should change, return {{}}.

Current form values:

{current_fields}

Today's date is:

{today}

The user said:

"{command}"

Determine which field(s) should be updated.

Rules:
- Return ONLY the fields that change.
- Keep field names exactly the same.
- Resolve relative dates (e.g. "next Monday") to YYYY-MM-DD.
- Do not invent new fields.
- If the request doesn't correspond to any field, return {{}}.

Example output:

{{
    "start_date": "2026-08-04"
}}
"""


def apply_edit_command(
    form,
    command: str,
    model: str | None = None,
    today: str | None = None,
):
    """
    Applies a natural-language edit command.

    Returns:
        updated_form, changed_fields
    """

    today_str = today or date.today().isoformat()

    current_fields = {
        key: value
        for key, value in form.model_dump().items()
        if key not in ("document_type", "missing_fields") and value is not None
    }

    prompt = EDIT_PROMPT.format(
        current_fields=json.dumps(current_fields, indent=2),
        today=today_str,
        command=command,
    )

    try:
        raw = chat_json(
            [{"role": "user", "content": prompt}],
            model=model,
        )

        changes = json.loads(raw)

    except json.JSONDecodeError:
        print("[edit_command] Invalid JSON returned:")
        print(raw)
        return form, []

    except Exception as e:
        print("[edit_command]", e)
        return form, []

    changed_fields = []

    for field, value in changes.items():
        if hasattr(form, field):
            setattr(form, field, value)
            changed_fields.append(field)

    form.compute_missing()

    return form, changed_fields