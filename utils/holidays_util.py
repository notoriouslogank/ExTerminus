"""Holiday helpers backed by the ``holidays`` library.

Provides:
    - ``holidays_for_month(year, month, state=None)``: mapping of ISO date strings (``YYYY-MM-DD``) to holiday names for the requested month.
    - ``is_holiday(date, state=None)``: return the holiday name for a date or ``None`` if it's not a holiday.

Notes:
    - Results of ``holidays_for_month`` are memoized with ``lru_cache`` to avoid repeated lookups during calendar rendering.
    - ``state`` can be a US state code (e.g., ``"CA"``, ``"VA"``) to include state-specific holidays.  Use ``None`` for federal-only recognition.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache

import holidays


@lru_cache(maxsize=64)
def holidays_for_month(
    year: int, month: int, state: str | None = None
) -> dict[str, str]:
    """Return holiday names for a given year/month as an ISO-date map.

    Uses the ``holidays`` package to compute US holidays, optionally including state-specific observances.

    Args:
        year (int): Four-digit year, e.g. ``2025``.
        month (int): Month number ``1..12``.
        state (str | None, optional): Two-letter state code (e.g., ``"VA"``).  If ``None``, only federal holidays are included.

    Returns:
        dict[str, str]: Mapping of ``"YYYY-MM-DD"`` to holiday name for all holidays that fall within the given month.
    """
    us = holidays.country_holidays("US", years=year, state=state)
    result: dict[str, str] = {}
    for d, name in us.items():
        if d.year == year and d.month == month:
            result[d.isoformat()] = name
    return result


def is_holiday(d: date, state: str | None = None) -> str | None:
    """Return the holiday name for ``d`` or ``None`` if not a holiday.

    Args:
        d (date): Date to check.
        state (str | None, optional): Two-letter state code to include state-specific holidays. Defaults to None.

    Returns:
        str | None: Holiday name if ``d`` is a holiday in that jurisdiction, otherwise ``None``.
    """
    return holidays_for_month(d.year, d.month, state).get(d.isoformat())
