import json
import os
from datetime import date

from pydantic import ValidationError

from src.extraction.schemas import DOCUMENT_SCHEMAS
from src.extraction.prompts import build_messages
from src.extraction.classify import classify
from src.extraction.normalize import (
    cross_check_duration,
    format_phone_number,
)
from src.extraction.llm_backend import chat_json
from src.utils.date_utils import parse_date


MODEL_NAME = os.getenv("GROQ_LLM_MODEL")
MAX_RETRIES = 2

PHONE_FIELDS = {
    "contact_number",
    "reference_number",
}

DATE_FIELDS = {
    "start_date",
}


def _call_llm(messages, model):
    """
    Calls the LLM backend.
    """
    return chat_json(messages, model=model)


def extract(
    transcript: str,
    today: str | None = None,
    model: str = MODEL_NAME,
    forced_doc_type: str | None = None,
):
    """
    Extract structured information from a transcript.

    Returns a Pydantic form object.
    """

    today_str = today or date.today().isoformat()

    #
    # Determine document type
    #
    if forced_doc_type:

        if forced_doc_type not in DOCUMENT_SCHEMAS:
            raise ValueError(
                f"UNKNOWN_DOCUMENT_TYPE: '{forced_doc_type}' is not supported."
            )

        doc_type = forced_doc_type

    else:

        doc_type = classify(
            transcript,
            model=model,
        )

        if doc_type == "no_intent":
            raise ValueError("NO_DOCUMENT_INTENT")

        if (
            doc_type == "unknown"
            or doc_type not in DOCUMENT_SCHEMAS
        ):
            raise ValueError("UNKNOWN_DOCUMENT_TYPE")

    #
    # Get schema
    #
    schema_cls = DOCUMENT_SCHEMAS[doc_type]

    #
    # Build extraction prompt
    #
    messages = build_messages(
        doc_type,
        transcript,
        today_str,
    )

    data = None
    last_error = None

    #
    # Retry extraction if JSON/schema is invalid
    #
    for attempt in range(MAX_RETRIES + 1):

        raw = _call_llm(
            messages,
            model,
        )

        try:

            candidate = json.loads(raw)

        except json.JSONDecodeError as e:

            last_error = str(e)

            messages.append(
                {
                    "role": "assistant",
                    "content": raw,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": "Return ONLY valid JSON.",
                }
            )

            continue

        #
        # Remove null values
        #
        candidate = {
            k: v
            for k, v in candidate.items()
            if v is not None
        }

        #
        # Normalize date fields immediately
        #
        for field in DATE_FIELDS:

            if (
                field in candidate
                and isinstance(candidate[field], str)
            ):

                parsed = parse_date(candidate[field])

                if parsed:
                    candidate[field] = parsed
                else:
                    candidate.pop(field, None)

        #
        # Validate against schema
        #
        try:

            schema_cls(**candidate)

            data = candidate

            break

        except ValidationError as e:

            last_error = str(e)

            messages.append(
                {
                    "role": "assistant",
                    "content": raw,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Return ONLY valid JSON matching the schema."
                    ),
                }
            )

            continue

    #
    # Extraction completely failed
    #
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

        if corrected:
            print(
                f"[extract] duration corrected: "
                f"{data.get('duration_days')} -> {duration}"
            )

        data["duration_days"] = duration

    else:

        data.pop("duration_days", None)

    #
    # Normalize start_date one final time
    #
    if "start_date" in data:

        parsed = parse_date(data["start_date"])

        if parsed:

            if parsed != data["start_date"]:

                print(
                    f"[extract] start_date normalized: "
                    f"{data['start_date']} -> {parsed}"
                )

            # Always keep ISO format
            data["start_date"] = parsed

        else:

            # Invalid date
            data.pop("start_date", None)

    #
    # Format phone numbers
    #
    for field in PHONE_FIELDS:

        if (
            field in data
            and isinstance(data[field], str)
        ):

            formatted = format_phone_number(
                data[field]
            )

            data[field] = formatted

    #
    # Build final form
    #
    form = schema_cls(**data)

    form.compute_missing()

    return form