from __future__ import annotations
from functools import lru_cache
from datetime import date
import holidays


@lru_cache(maxsize=64)
def holidays_for_month(
    year: int, month: int, state: str | None = None
) -> dict[str, str]:
    us = holidays.country_holidays("US", years=year, state=state)
    result: dict[str, str] = {}
    for d, name in us.items():
        if d.year == year and d.month == month:
            result[d.isoformat()] = name
    return result


def is_holiday(d: date, state: str | None = None) -> str | None:
    return holidays_for_month(d.year, d.month, state).get(d.isoformat())
