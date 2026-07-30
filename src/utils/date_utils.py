from datetime import date
import dateparser


def parse_date(text: str) -> str | None:
    """
    Convert natural language dates into ISO format (YYYY-MM-DD).
    """

    if not text:
        return None

    text = text.strip()

    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        pass

    parsed = dateparser.parse(
        text,
        settings={
            "PREFER_DATES_FROM": "future",
            "DATE_ORDER": "DMY",
        },
    )

    if parsed:
        return parsed.date().isoformat()

    return None


def format_date(text: str) -> str:
    """
    Convert any supported date into '26 August 2026'.
    """

    iso = parse_date(text)

    if not iso:
        raise ValueError(f"Invalid date: {text}")

    d = date.fromisoformat(iso)
    return d.strftime("%d %B %Y")