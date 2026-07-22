import json
from datetime import date
import ollama
from pydantic import ValidationError

from src.extraction.schemas import DOCUMENT_SCHEMAS
from src.extraction.prompts import build_messages
from src.extraction.classify import classify
from src.extraction.normalize import cross_check_duration, resolve_relative_date, validate_iso_date

MODEL_NAME = "llama3.2"
MAX_RETRIES = 2


def cross_check_start_date(transcript: str, llm_extracted_value, today: date) -> tuple:
    llm_valid = llm_extracted_value is not None and validate_iso_date(llm_extracted_value)
    if llm_valid:
        return llm_extracted_value, False
    rule_based_value = resolve_relative_date(transcript, today)
    if rule_based_value is not None:
        return rule_based_value, True
    return None, False


def _call_llm(messages: list[dict], model: str) -> str:
    response = ollama.chat(model=model, messages=messages, format="json", options={"temperature": 0})
    return response["message"]["content"]


def extract(transcript: str, today: str | None = None, model: str = MODEL_NAME,
            forced_doc_type: str | None = None):
    today_str = today or date.today().isoformat()
    today_date = date.fromisoformat(today_str)

    if forced_doc_type:
        if forced_doc_type not in DOCUMENT_SCHEMAS:
            raise ValueError(f"UNKNOWN_DOCUMENT_TYPE: '{forced_doc_type}' is not a supported document type.")
        doc_type = forced_doc_type
    else:
        doc_type = classify(transcript, model=model)
        if doc_type == "no_intent":
            raise ValueError(
                "NO_DOCUMENT_INTENT: I couldn't find a request for any document in that. "
                "Try describing what you need — e.g. 'I need 3 days leave...' or "
                "'I want to file a complaint about...'"
            )
        if doc_type == "unknown" or doc_type not in DOCUMENT_SCHEMAS:
            raise ValueError(
                "UNKNOWN_DOCUMENT_TYPE: What kind of document do you need? "
                "(office leave, university leave, or complaint letter)"
            )

    schema_cls = DOCUMENT_SCHEMAS[doc_type]
    messages = build_messages(doc_type, transcript, today_str)

    last_error = None
    data = None

    for attempt in range(MAX_RETRIES + 1):
        raw = _call_llm(messages, model)
        try:
            candidate = json.loads(raw)
        except json.JSONDecodeError as e:
            last_error = f"Invalid JSON: {e}"
            print(f"[extract] attempt {attempt + 1}/{MAX_RETRIES + 1} — JSON parse failed. Raw:\n{raw}")
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content":
                f"Your last response was not valid JSON ({e}). Return ONLY a valid JSON object "
                f"matching the required schema, with no extra text."})
            continue

        candidate = {k: v for k, v in candidate.items() if v is not None}

        try:
            schema_cls(**candidate)
            data = candidate
            break
        except ValidationError as e:
            last_error = f"Schema validation failed: {e}"
            print(f"[extract] attempt {attempt + 1}/{MAX_RETRIES + 1} — schema validation failed:\n{e}")
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content":
                f"Your last response failed schema validation: {e}. "
                f"Return ONLY a valid JSON object matching the required schema exactly."})
            continue

    if data is None:
        raise ValueError(
            f"EXTRACTION_FAILED: Could not extract valid data after {MAX_RETRIES + 1} attempts. "
            f"Last error: {last_error}"
        )

    corrected_duration, duration_corrected = cross_check_duration(transcript, data.get("duration_days"))
    if duration_corrected:
        print(f"[extract] duration_days corrected by normalize layer: "
              f"{data.get('duration_days')} -> {corrected_duration}")
    if corrected_duration is not None:
        data["duration_days"] = corrected_duration
    elif "duration_days" in data:
        del data["duration_days"]

    corrected_date, date_corrected = cross_check_start_date(transcript, data.get("start_date"), today_date)
    if date_corrected:
        print(f"[extract] start_date corrected by normalize layer: "
              f"{data.get('start_date')} -> {corrected_date}")
    if corrected_date is not None:
        data["start_date"] = corrected_date
    elif "start_date" in data:
        del data["start_date"]

    form = schema_cls(**data)
    form.compute_missing()
    return form


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "I need 3 days leave starting Monday"
    result = extract(text)
    print(result.model_dump_json(indent=2))