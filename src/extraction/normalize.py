import re
from datetime import date, timedelta

URDU_NUMBERS = {
    "aik": 1, "ek": 1, "one": 1, "ایک": 1,
    "do": 2, "two": 2, "دو": 2,
    "teen": 3, "three": 3, "تین": 3,
    "char": 4, "chaar": 4, "four": 4, "چار": 4,
    "paanch": 5, "panch": 5, "five": 5, "پانچ": 5,
    "chey": 6, "che": 6, "six": 6, "چھ": 6,
    "saat": 7, "seven": 7, "سات": 7,
    "aath": 8, "eight": 8, "آٹھ": 8,
    "nau": 9, "nine": 9, "نو": 9,
    "das": 10, "dus": 10, "ten": 10, "دس": 10,
}

URDU_DAY_NUMBERS = {
    "ایک": 1, "دو": 2, "تین": 3, "چار": 4, "پانچ": 5,
    "چھ": 6, "سات": 7, "آٹھ": 8, "نو": 9, "دس": 10,
    "گیارہ": 11, "بارہ": 12, "تیرہ": 13, "چودہ": 14, "پندرہ": 15,
    "سولہ": 16, "سترہ": 17, "اٹھارہ": 18, "انیس": 19, "بیس": 20,
    "اکیس": 21, "بائیس": 22, "تیئس": 23, "چوبیس": 24, "پچیس": 25,
    "چھبیس": 26, "ستائیس": 27, "اٹھائیس": 28, "انتیس": 29, "تیس": 30,
    "اکتیس": 31,
}

ROMAN_DAY_NUMBERS = {
    "aik": 1, "ek": 1, "do": 2, "teen": 3, "chaar": 4, "char": 4,
    "paanch": 5, "panch": 5, "che": 6, "chey": 6, "saat": 7,
    "aath": 8, "nau": 9, "das": 10, "dus": 10, "gyarah": 11,
    "baarah": 12, "terah": 13, "chaudah": 14, "pandrah": 15,
    "solah": 16, "satrah": 17, "athara": 18, "unnees": 19,
    "bees": 20, "ikkis": 21, "bais": 22, "teis": 23, "chaubis": 24,
    "pachis": 25, "chabbis": 26, "sataais": 27, "athaais": 28,
    "untees": 29, "tees": 30, "ikatees": 31,
}

DAY_WORDS = ["din", "day", "days", "دن"]

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
        pattern = rf"\b{re.escape(word)}\b\s*(din|day|days|دن)\b|\b(din|day|days|دن)\b\s*\b{re.escape(word)}\b"
        if re.search(pattern, text_lower):
            return value

    duration_unit_pattern = r"\b(\d+)\s*(din|days?|hafte|weeks?|mahine|months?|دن)\b"
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

    day_of_month_result = resolve_day_of_month(text_lower, today)
    if day_of_month_result:
        return day_of_month_result

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

def resolve_day_of_month(text: str, today: date) -> str | None:
    text_lower = text.lower()

    digit_pattern = r"\b(\d{1,2})\s*(tareekh|تاریخ)\b"
    match = re.search(digit_pattern, text_lower)
    day = None
    if match:
        day = int(match.group(1))
    else:
        all_day_words = {**URDU_DAY_NUMBERS, **ROMAN_DAY_NUMBERS}
        for word, value in all_day_words.items():
            pattern = rf"\b{re.escape(word)}\b\s*(تاریخ|tareekh)"
            if re.search(pattern, text_lower):
                day = value
                break

    if day is None or not (1 <= day <= 31):
        return None

    try:
        candidate = today.replace(day=day)
    except ValueError:
        return None

    if candidate < today:
        if today.month == 12:
            candidate = candidate.replace(year=today.year + 1, month=1)
        else:
            candidate = candidate.replace(month=today.month + 1)

    return candidate.isoformat()

def format_phone_number(raw: str) -> str:
    """Normalize Pakistani mobile numbers to 0300-1234567 format if 11 digits detected."""
    digits = re.sub(r"[^\d]", "", raw)
    if len(digits) == 11 and digits.startswith("0"):
        return f"{digits[:4]}-{digits[4:]}"
    return raw