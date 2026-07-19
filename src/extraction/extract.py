"""extract(transcript) -> FormJSON, using a local Ollama model. No API key needed."""
import json
from datetime import date
import ollama

from src.extraction.schemas import DOCUMENT_SCHEMAS, LeaveApplicationForm
from src.extraction.prompts import build_messages

MODEL_NAME = "llama3.2"  


def extract(transcript: str, today: str | None = None, model: str = MODEL_NAME) -> LeaveApplicationForm:
    """
    Extract structured fields from a transcript using a local Ollama model.
    today: ISO date string used to resolve relative expressions. Defaults to real today.
    """
    today = today or date.today().isoformat()
    messages = build_messages(transcript, today)

    response = ollama.chat(
        model=model,
        messages=messages,
        format="json",  
        options={"temperature": 0},
    )

    raw = response["message"]["content"]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[extract] JSON parse failed. Raw output:\n{raw}")
        raise e

    doc_type = data.get("document_type", "leave_application")
    schema_cls = DOCUMENT_SCHEMAS.get(doc_type, LeaveApplicationForm)

    form = schema_cls(**data)
    form.compute_missing()
    return form


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "I need 3 days leave starting Monday, my sister is getting married"
    result = extract(text)
    print(result.model_dump_json(indent=2))