import json
import os
from datetime import date
from pydantic import ValidationError
import dateparser

from src.extraction.schemas import DOCUMENT_SCHEMAS
from src.extraction.prompts import build_messages
from src.extraction.classify import classify
from src.extraction.normalize import (
    cross_check_duration,
    format_phone_number,
)

from src.utils.date_utils import parse_date
from src.extraction.llm_backend import chat_json


MODEL_NAME = os.getenv("GROQ_LLM_MODEL")
MAX_RETRIES = 2

PHONE_FIELDS = {"contact_number", "reference_number"}
DATE_FIELDS = {"start_date"}


def parse_flexible_date(text: str):
    """
    Converts almost any natural language date into YYYY-MM-DD.

    Examples
    --------
    tomorrow
    next monday
    monday
    26 august 2026
    26 aug 2026
    26/08/2026
    """

    if not text:
        return None

    if isinstance(text, date):
        return text.isoformat()

    text = str(text).strip()

    # Already ISO
    try:
        return date.fromisoformat(text).isoformat()
    except Exception:
        pass

    parsed = dateparser.parse(
        text,
        settings={
            "PREFER_DATES_FROM": "future",
            "DATE_ORDER": "DMY",
            "RELATIVE_BASE": date.today(),
        },
    )

    if parsed:
        return parsed.date().isoformat()

    return None





def _call_llm(messages, model):
    return chat_json(messages, model=model)


def extract(
    transcript: str,
    today: str | None = None,
    model: str = MODEL_NAME,
    forced_doc_type: str | None = None,
):
    today_str = today or date.today().isoformat()

    if forced_doc_type:
        if forced_doc_type not in DOCUMENT_SCHEMAS:
            raise ValueError(
                f"UNKNOWN_DOCUMENT_TYPE: '{forced_doc_type}' is not supported."
            )
        doc_type = forced_doc_type

    else:
        doc_type = classify(transcript, model=model)

        if doc_type == "no_intent":
            raise ValueError("NO_DOCUMENT_INTENT")

        if doc_type == "unknown" or doc_type not in DOCUMENT_SCHEMAS:
            raise ValueError("UNKNOWN_DOCUMENT_TYPE")

    schema_cls = DOCUMENT_SCHEMAS[doc_type]

    messages = build_messages(
        doc_type,
        transcript,
        today_str,
    )

    data = None
    last_error = None

    for attempt in range(MAX_RETRIES + 1):

        raw = _call_llm(messages, model)

        try:
            candidate = json.loads(raw)

        except json.JSONDecodeError as e:

            last_error = str(e)

            messages.append(
                {"role": "assistant", "content": raw}
            )

            messages.append(
                {
                    "role": "user",
                    "content": "Return ONLY valid JSON.",
                }
            )

            continue

        candidate = {
            k: v
            for k, v in candidate.items()
            if v is not None
        }
        if "start_date" in candidate and isinstance(candidate["start_date"], str):
          parsed = parse_date(candidate["start_date"])
          if parsed:
            candidate["start_date"] = parsed

        for field in DATE_FIELDS:

            if field in candidate and isinstance(candidate[field], str):

                parsed = parse_flexible_date(candidate[field])

                if parsed:
                    candidate[field] = parsed

        try:

            schema_cls(**candidate)

            data = candidate

            break

        except ValidationError as e:

            last_error = str(e)

            messages.append(
                {"role": "assistant", "content": raw}
            )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Return ONLY valid JSON matching the schema."
                    ),
                }
            )

    if data is None:
        raise ValueError(
            f"EXTRACTION_FAILED: {last_error}"
        )

    #
    # Cross-check duration
    #
    duration, corrected = cross_check_duration(
        transcript,
        data.get("duration_days"),
    )

    if duration is not None:
        data["duration_days"] = duration

    elif "duration_days" in data:
        del data["duration_days"]

    #
    # Cross-check date
    #
    if "start_date" in data:
     parsed = parse_date(data["start_date"])

     if parsed:
            if parsed != data["start_date"]:
               print(
                  f"[extract] start_date normalized: "
                  f"{data['start_date']} -> {parsed}"
                )

               data["start_date"] = parsed
            else:
                del data["start_date"]

    #
    # Format phone numbers
    #
    for field in PHONE_FIELDS:

        if field in data and isinstance(data[field], str):

            data[field] = format_phone_number(data[field])

    form = schema_cls(**data)

    form.compute_missing()

    return form


if __name__ == "__main__":

    result = extract(
        "I need leave starting next monday for 3 days."
    )

    print(result.model_dump_json(indent=2))