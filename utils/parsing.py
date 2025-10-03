from datetime import date, datetime
from typing import Optional


def parse_date(s: str | None) -> Optional[date]:

    if s:

        return datetime.strptime(s, "%Y-%m-%d").date()

    else:
        return None


def parse_time(s: str | None) -> Optional[str]:
    if not s:
        return None
    datetime.strptime(s, "%H:%M")


def parse_int(s: str | None) -> Optional[int]:
    try:
        return int(s) if s else None
    except ValueError:
        return None
