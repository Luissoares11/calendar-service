import os
from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE = os.getenv("TIMEZONE", "Europe/Lisbon")


def _now() -> datetime:
    """Get current time in the configured timezone."""
    return datetime.now(ZoneInfo(TIMEZONE))


def _parse_datetime(date_str: str, time_str: str = "09:00") -> datetime:
    """
    Parse date and time strings into a datetime object.

    Supports multiple date formats:
    - DD/MM/YYYY
    - YYYY-MM-DD
    - DD-MM-YYYY
    """
    # Try different date formats
    date_formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
    dt = None

    for fmt in date_formats:
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", f"{fmt} %H:%M")
            break
        except ValueError:
            continue

    if dt is None:
        raise ValueError(f"Could not parse date '{date_str}'. Use DD/MM/YYYY, YYYY-MM-DD, or DD-MM-YYYY.")

    # Attach timezone
    dt = dt.replace(tzinfo=ZoneInfo(TIMEZONE))
    return dt
