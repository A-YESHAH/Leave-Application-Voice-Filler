import re
from datetime import date, timedelta

URDU_NUMBERS = {
    "aik": 1, "ek": 1, "one": 1,
    "do": 2, "two": 2,
    "teen": 3, "three": 3,
    "char": 4, "chaar": 4, "four": 4,
    "paanch": 5, "panch": 5, "five": 5,
    "chey": 6, "che": 6, "six": 6,
    "saat": 7, "seven": 7,
    "aath": 8, "eight": 8,
    "nau": 9, "nine": 9,
    "das": 10, "dus": 10, "ten": 10,
}

RELATIVE_DATE_OFFSETS = {
    "aaj": 0, "today": 0,
    "kal": 1,
    "parson": 2, "parso": 2,
    "agla hafte": 7, "agle hafte": 7, "next week": 7,
    "agla mahina": 30, "agle mahine": 30, "next month": 30,
}

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def extract_number_word(text: str) -> int | None:
    text_lower = text.lower()

    for word, value in URDU_NUMBERS.items():
        if re.search(rf"\b{re.escape(word)}\b", text_lower):
            return value

    duration_unit_pattern = r"\b(\d+)\s*(din|days?|hafte|weeks?|mahine|months?)\b"
    digit_match = re.search(duration_unit_pattern, text_lower)
    if digit_match:
        return int(digit_match.group(1))

    return None


def resolve_weekday(text: str, today: date) -> str | None:
    text_lower = text.lower()
    for name, weekday_num in WEEKDAYS.items():
        if name in text_lower:
            days_ahead = (weekday_num - today.weekday() + 7) % 7
            days_ahead = days_ahead or 7
            return (today + timedelta(days=days_ahead)).isoformat()
    return None


def resolve_relative_date(text: str, today: date, assume_future: bool = True) -> str | None:
    text_lower = text.lower()

    weekday_result = resolve_weekday(text_lower, today)
    if weekday_result:
        return weekday_result

    for phrase, offset in RELATIVE_DATE_OFFSETS.items():
        if phrase in text_lower:
            if phrase in ("kal",) and not assume_future:
                offset = -1
            return (today + timedelta(days=offset)).isoformat()

    return None


def validate_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def cross_check_duration(transcript: str, llm_extracted_value: int | None) -> tuple[int | None, bool]:
    rule_based_value = extract_number_word(transcript)

    if llm_extracted_value is None and rule_based_value is not None:
        return rule_based_value, True

    if llm_extracted_value is not None and rule_based_value is not None:
        if llm_extracted_value != rule_based_value:
            return rule_based_value, True
        return llm_extracted_value, False

    return llm_extracted_value, False