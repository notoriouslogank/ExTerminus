"""Calendar routes: month and day views, time off management, and lock toggles.

Exposes:
- GET  /                    -> month view (index)
- GET  /day/<date>          -> day view
- GET/POST /timeoff/add     -> add time off
- POST /lock/toggle         -> lock/unlock a day

Notes:
    Uses state code ``VA`` for holidays via ``holidays_for_month``.
"""

from calendar import Calendar, month_name, monthrange
from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..db import get_database
from ..utils.decorators import login_required, role_required
from ..utils.holidays_util import holidays_for_month
from ..utils.logger import setup_logger

calendar_bp = Blueprint("calendar", __name__)
log = setup_logger()


def _month_weeks(year: int, month: int, firstweekday: int = 6) -> list[list[date]]:
    """Return a month as a list of week rows, each a list of 7 dates.

    Wraps ``calendar.Calendar.itermonthdates`` and chunks into 70day rows.  ``firstweekday=6`` means weeks start on Sunday.

    Args:
        year (int): Four-digit year.
        month (int): Month number (1-12).
        firstweekday (int, optional): 0=Monday ... 6=Sunday. Defaults to 6.

    Returns:
        list[list[date]]: Weeks covering the requested month (spillover days from adjacent months included to fill full weeks).
    """
    cal = Calendar(firstweekday=firstweekday)
    days = list(cal.itermonthdates(year, month))
    return [days[i : i + 7] for i in range(0, len(days), 7)]


def _expand_multi_day(sd_str: str, ed_str: str | None):
    """Yield each date in a job's inclusive span.

    Args:
        sd_str (str): Start date in ISO ``YYYY-MM-DD``.
        ed_str (str | None): End date in ISO ``YYYY-MM-DD`` (or None for single-day jobs).

    Yields:
        date: Each date from start through end (inclusive).
    """
    sd = datetime.fromisoformat(sd_str).date()
    ed = datetime.fromisoformat(ed_str).date() if ed_str else sd
    d = sd
    while d <= ed:
        yield d
        d += timedelta(days=1)


@calendar_bp.route("/", endpoint="index")
def index():
    """Render the month (calendar) view.

    Query args:
        month (int, optional): 1-12; defaults to current month.
        year (int, optional): Four-digit year; defaults to current year.

    Behavior:
        - Computes month boundaries and week grid.
        - Loads day locks and jobs spanning the month (inclusive).
        - Expands multi-day jobs to each date for rendering.
        - Loads technician time off and expands to each date.
        - Computes holiday map for the month (state ``"VA"``).
        - Passes type abbreviations to the template.

    Returns:
        Response: Rendered ``index.html`` with calendar context.
    """
    today = date.today()
    month = request.args.get("month", type=int, default=today.month)
    year = request.args.get("year", type=int, default=today.year)

    month_start = date(year, month, 1)
    month_end = date(year, month, monthrange(year, month)[1])

    month_start_s = month_start.isoformat()
    month_end_s = month_end.isoformat()

    weeks = _month_weeks(year, month)

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    conn = get_database()
    cur = conn.cursor()

    cur.execute("SELECT date FROM locks")
    locks = {row["date"] for row in cur.fetchall()}

    jobs_by_date = {}
    time_off_by_date = {}

    cur.execute(
        """
        SELECT
            j.id,
            j.title,
            j.job_type AS type,
            j.price,
            j.start_date,
            j.end_date,
            j.start_time,
            j.end_time,
            j.time_range,
            j.rei_quantity AS rei_quantity,
            j.rei_zip AS rei_zip,
            j.rei_city_name AS rei_city_name,
            j.technician_id,
            j.two_man,
            t.name AS technician_name,
            CASE
                WHEN j.two_man = 1 THEN 'Two Man'
                WHEN t.name IS NOT NULL THEN t.name
                ELSE ''
            END AS technician_label
        FROM jobs j
        LEFT JOIN technicians t ON t.id = j.technician_id
        WHERE j.start_date <= ?
            AND (j.end_date IS NULL OR j.end_date >= ?);
        """,
        (month_end_s, month_start_s),
    )

    for job in cur.fetchall():
        for d in _expand_multi_day(job["start_date"], job["end_date"]):
            jobs_by_date.setdefault(d.isoformat(), []).append(job)

    cur.execute(
        """
        SELECT toff.start_date, toff.end_date, tech.name AS technician_name
        FROM time_off toff
        JOIN technicians tech ON tech.id = toff.technician_id
        """
    )
    time_off_by_date: dict[str, list[str]] = {}
    for row in cur.fetchall():
        for d in _expand_multi_day(row["start_date"], row["end_date"]):
            time_off_by_date.setdefault(d.isoformat(), []).append(
                row["technician_name"]
            )

    conn.close()

    holidays = {}

    TYPE_ABBR = {
        "fumigation": "F",
        "insulation": "I",
        "exclusion": "EX",
        "rei": "REIs",
        "borate": "B",
        "bird work": "BW",
        "poly": "P",
        "power spray": "PS",
    }

    STATE_CODE = "VA"
    holidays_map = holidays_for_month(year, month, state=STATE_CODE)

    return render_template(
        "index.html",
        weeks=weeks,
        month=month,
        year=year,
        month_name=month_name[month],
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        locks=locks,
        jobs_by_date=jobs_by_date,
        time_off_by_date=time_off_by_date,
        today=today,
        type_abbr=TYPE_ABBR,
        holidays=holidays_map,
    )


@calendar_bp.route("/day/<selected_date>", endpoint="day_view")
def day_view(selected_date: str):
    """Render the day view for a specific date.

    Args:
        selected_date (str): ISO date (``YYYY-MM-DD``) from the route segment.

    Behavior:
        - Redirects to month view if the date is invalid.
        - Loads lock status and all jobs overlapping the date.
        - Joins creator/modifier usernames for the audit block.
        - Normalizes REI titles to display label ``"REIs"``.

    Returns:
        Response: Rendered ``day.html`` with jobs and lock status.
    """
    try:
        dt = datetime.fromisoformat(selected_date).date()
    except Exception:
        return redirect(url_for("calendar.index"))

    conn = get_database()
    import sqlite3

    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM locks WHERE date = ?", (selected_date,))
    locked = cur.fetchone() is not None

    cur.execute(
        """
        SELECT
            j.*,
            j.job_type AS type,
            j.rei_quantity AS rei_quantity,
            j.rei_zip AS rei_zip,
            j.rei_city_name AS rei_city_name,
            t.name AS technician_name,
            cu.username AS created_by_name,
            mu.username AS modified_by_name,
            CASE
                WHEN LOWER(COALESCE(j.job_type, '')) = 'rei' THEN 'REIs'
                ELSE COALESCE(NULLIF(j.title, ''), '(Untitled)')
            END AS display_title
        FROM jobs j
        LEFT JOIN technicians t ON t.id = j.technician_id
        LEFT JOIN users cu ON cu.id = j.created_by
        LEFT JOIN users mu ON mu.id = j.last_modified_by
        WHERE j.start_date <= ? AND (j.end_date IS NULL OR j.end_date >= ?)
        ORDER BY j.start_date, j.id
        """,
        (selected_date, selected_date),
    )
    jobs = cur.fetchall()

    conn.close()
    return render_template("day.html", selected_date=dt, locked=locked, jobs=jobs)


@calendar_bp.route("/timeoff/add", methods=["GET", "POST"], endpoint="add_time_off")
@login_required
@role_required("admin", "manager", "technician")
def add_time_off():
    """Create a time off entry for a technician.

    Handles GET (render form) and POST (submit).  Requires role admin/manage/technician.  On POST, validates fields and inserts into ``time_off``.

    Returns:
        Response: On success, redirect to ``calendar.index``.  On validation errors, redirect back to ``calendar.add_time_off``.  On GET, render form.
    """
    if "user" not in session:
        return redirect(url_for("auth.login"))

    conn = get_database()
    cur = conn.cursor()

    if request.method == "POST":
        technician_id = request.form.get("technician_id")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        reason = request.form.get("reason")

        if not technician_id or not start_date or not end_date:
            flash("All fields are required.", "error")
            return redirect(url_for("calendar.add_time_off"))

        cur.execute(
            "INSERT INTO time_off (technician_id, start_date, end_date, reason) VALUES (?, ?, ?, ?)",
            (technician_id, start_date, end_date, reason),
        )
        conn.commit()
        flash("Time off added.", "success")
        return redirect(url_for("calendar.index"))

    cur.execute("SELECT id, name FROM technicians ORDER BY name")
    technicians = cur.fetchall()
    conn.close()
    return render_template("add_time_off.html", technicians=technicians)


@calendar_bp.route("/lock/toggle", methods=["POST"], endpoint="toggle_lock")
@login_required
@role_required("admin", "manager", "technician")
def toggle_lock():
    """Toggle the lock status for a specific date.

    Reads the target date from form field ``date``.  If locked, unlocks it; if unlocked, inserts a lock with the current user's ID.

    Returns:
        Response: Redirect to ``calendar.day_view`` for the selected date.  On missing date, redirects to ``calendar.index`` with a flash error.
    """
    selected_date = request.form.get("date")
    if not selected_date:
        flash("No date provided.", "error")
        return redirect(url_for("calendar.index"))

    user = session.get("user")
    user_id = user["id"] if isinstance(user, dict) and "id" in user else None

    conn = get_database()
    cur = conn.cursor()

    cur.execute("SELECT id FROM locks WHERE date = ?", (selected_date,))
    row = cur.fetchone()

    if row:
        cur.execute("DELETE FROM locks WHERE date = ?", (selected_date,))
        conn.commit()
        flash(f"Unlocked {selected_date}.", "success")
    else:
        cur.execute(
            "INSERT INTO locks (date, locked_by) VALUES (?, ?)",
            (selected_date, user_id),
        )
        conn.commit()
        flash(f"Locked {selected_date}.", "success")

    conn.close()
    return redirect(url_for("calendar.day_view", selected_date=selected_date))
