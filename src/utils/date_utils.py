import difflib
from datetime import date, datetime, timedelta
import dateparser

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

# Minimum similarity ratio (0-1) for a misspelled weekday to be accepted.
WEEKDAY_FUZZY_CUTOFF = 0.75


def _next_weekday(today: date, weekday: int) -> date:
    days = (weekday - today.weekday()) % 7
    if days == 0:
        days = 7
    return today + timedelta(days=days)


def _match_weekday(word: str) -> int | None:
    """
    Resolves a (possibly misspelled) weekday name to its index.

    Tries an exact match first, then falls back to a fuzzy match so
    typos like "moday" or "tuesady" still resolve correctly.
    """

    if word in WEEKDAYS:
        return WEEKDAYS[word]

    close = difflib.get_close_matches(
        word,
        WEEKDAYS.keys(),
        n=1,
        cutoff=WEEKDAY_FUZZY_CUTOFF,
    )

    if close:
        return WEEKDAYS[close[0]]

    return None


def parse_date(text: str) -> str | None:
    """
    Converts many date formats into YYYY-MM-DD.

    Supports:
    - today
    - tomorrow
    - next Monday
    - Monday
    - 26 August 2026
    - 26 Aug 2026
    - 26/08/2026
    - 26-08-2026
    - 2026-08-26
    """

    if not text:
        return None

    text = text.strip()
    lower = text.lower()

    today = date.today()

    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        pass

    if lower == "today":
        return today.isoformat()

    if lower == "tomorrow":
        return (today + timedelta(days=1)).isoformat()

    weekday_word = lower
    if weekday_word.startswith("next "):
        weekday_word = weekday_word[len("next "):].strip()

    weekday_number = _match_weekday(weekday_word)

    if weekday_number is not None:
        return _next_weekday(today, weekday_number).isoformat()

    parsed = dateparser.parse(
        text,
        settings={
            "PREFER_DATES_FROM": "future",
            "DATE_ORDER": "DMY",
        },
    )

    if parsed:
        return parsed.date().isoformat()

    for fmt in (
        "%d %B %Y",
        "%d %b %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass

    return None


def format_date(text: str) -> str:
    """
    Converts any supported date into:
    26 August 2026
    """

    iso = parse_date(text)

    if iso is None:
        raise ValueError(f"Invalid date: {text}")

    return date.fromisoformat(iso).strftime("%d %B %Y")