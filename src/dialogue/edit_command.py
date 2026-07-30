import json
import os
from datetime import date

from src.extraction.llm_backend import chat_json

DEFAULT_MODEL = os.getenv("GROQ_LLM_MODEL")

EDIT_PROMPT = """..."""

def apply_edit_command(
    form,
    command: str,
    model: str | None = DEFAULT_MODEL,
    today: str | None = None,
):
    today_str = today or date.today().isoformat()

    current_fields = {
        k: v
        for k, v in form.model_dump().items()
        if k not in ("document_type", "missing_fields") and v is not None
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
    for field, new_value in changes.items():
        if hasattr(form, field):
            setattr(form, field, new_value)
            changed_fields.append(field)

    form.compute_missing()
    return form, changed_fields