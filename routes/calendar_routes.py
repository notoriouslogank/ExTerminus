"""Calendar routes: month and day views, time off management, and lock toggles.

Exposes:
- GET  /                    -> month view (index)
- GET  /day/<date>          -> day view
- POST /time_off/add        -> add time off
- POST /lock/toggle         -> lock/unlock a day

Notes:
    Uses state code ``VA`` for holidays via ``holidays_for_month``.
"""

from collections import defaultdict
from calendar import Calendar, month_name
from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db import get_database
from utils.decorators import login_required, role_required
from utils.holidays_util import holidays_for_month
from utils.logger import setup_logger

calendar_bp = Blueprint("calendar", __name__)
log = setup_logger()


def _month_weeks(year: int, month: int, firstweekday: int = 6) -> list[list[date]]:
    """Return a month as a list of week rows, each a list of 7 dates (Sunday-first by default)."""
    cal = Calendar(firstweekday=firstweekday)
    days = list(cal.itermonthdates(year, month))
    return [days[i : i + 7] for i in range(0, len(days), 7)]


def _expand_multi_day(sd_str: str, ed_str: str | None):
    """Yield each date in a job's inclusive span."""
    sd = datetime.fromisoformat(sd_str).date()
    ed = datetime.fromisoformat(ed_str).date() if ed_str else sd
    d = sd
    while d <= ed:
        yield d
        d += timedelta(days=1)


@calendar_bp.route("/", endpoint="index")
def index():
    today = date.today()
    month = request.args.get("month", type=int, default=today.month)
    year = request.args.get("year", type=int, default=today.year)

    # build week grid
    weeks = _month_weeks(year, month, firstweekday=6)
    grid_start = weeks[0][0]
    grid_end = weeks[-1][-1]
    grid_start_s, grid_end_s = grid_start.isoformat(), grid_end.isoformat()

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    conn = get_database()
    cur = conn.cursor()

    # Locks spanning the visible grid
    cur.execute(
        "SELECT date FROM locks WHERE date BETWEEN ? AND ?",
        (grid_start_s, grid_end_s),
    )
    locks = {row["date"] for row in cur.fetchall()}

    # Jobs spanning the visible grid
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
        WHERE date(j.start_date) <= date(:grid_end)
          AND date(COALESCE(j.end_date, j.start_date)) >= date(:grid_start)
        """,
        {"grid_start": grid_start_s, "grid_end": grid_end_s},
    )

    jobs_by_date: dict[str, list] = defaultdict(list)
    for job in cur.fetchall():
        sd = datetime.fromisoformat(job["start_date"]).date()
        ed = datetime.fromisoformat(job["end_date"]).date() if job["end_date"] else sd
        start = sd if sd >= grid_start else grid_start
        end = ed if ed <= grid_end else grid_end
        d = start
        while d <= end:
            jobs_by_date[d.isoformat()].append(job)
            d += timedelta(days=1)

    # --- Time off for the grid (OBJECTS, not just names) ---
    cur.execute(
        """
        SELECT
          toff.id,
          toff.technician_id AS owner_id,
          toff.start_date,
          COALESCE(toff.end_date, toff.start_date) AS end_date,
          tech.name AS name
        FROM time_off AS toff
        JOIN technicians AS tech ON tech.id = toff.technician_id
        WHERE date(toff.start_date) <= date(:grid_end)
          AND date(COALESCE(toff.end_date, toff.start_date)) >= date(:grid_start)
        """,
        {"grid_start": grid_start_s, "grid_end": grid_end_s},
    )

    time_off_by_date: dict[str, list[dict]] = defaultdict(list)
    for row in cur.fetchall():
        sd = datetime.fromisoformat(row["start_date"]).date()
        ed = datetime.fromisoformat(row["end_date"]).date()
        start = sd if sd >= grid_start else grid_start
        end = ed if ed <= grid_end else grid_end
        d = start
        while d <= end:
            time_off_by_date[d.isoformat()].append(
                {"id": row["id"], "owner_id": row["owner_id"], "name": row["name"]}
            )
            d += timedelta(days=1)

    conn.close()

    STATE_CODE = "VA"
    holidays_map = holidays_for_month(year, month, state=STATE_CODE)

    TYPE_ABBR = {
        "termite": "T",
        "borate": "BOR",
        "pretreat": "PT",
        "retreat": "RT",
        "bird work": "BRD",
        "power spray": "PS",
        "fumigation": "FUME",
        "insulation": "INSU",
        "exclusion": "EXC",
        "rei": "REIs",
        "reis": "REIs",
        "pest control special service": "PCSS",
        "vapor barrier": "VAPR",
        "shop work": "SHOP",
        "misc": "MISC",
        "miscellaneous": "MISC",
    }

    return render_template(
        "index.html",
        weeks=weeks,
        month=month,
        year=year,
        month_name=month_name[month],
        prev_month=prev_month,
        next_month=next_month,
        prev_year=prev_year,
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
    """Render the day view for a specific date."""
    try:
        dt = datetime.fromisoformat(selected_date).date()
    except Exception:
        return redirect(url_for("calendar.index"))

    conn = get_database()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM locks WHERE date = ?", (selected_date,))
    locked = cur.fetchone() is not None

    # Day-specific time off (list of rows)
    cur.execute(
        """
        SELECT
          toff.id,
          toff.technician_id AS owner_id,
          tech.name AS tech_name,
          toff.reason
        FROM time_off AS toff
        LEFT JOIN technicians AS tech ON tech.id = toff.technician_id
        WHERE date(:sel) BETWEEN date(toff.start_date)
                            AND date(COALESCE(toff.end_date, toff.start_date))
        ORDER BY tech.name
        """,
        {"sel": selected_date},
    )
    time_off = cur.fetchall()

    # Jobs overlapping the day
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
    return render_template(
        "day.html",
        default_date=request.args.get("date") or date.today().isoformat(),
        selected_date=dt,
        locked=locked,
        jobs=jobs,
        time_off=time_off,
    )


@calendar_bp.route("/time_off/add", methods=["POST"])
@login_required
def add_time_off():
    """Add time off. Defaults: end_date=start_date; start_date=today if missing."""
    user = session["user"]
    start = (request.form.get("start_date") or "").strip()
    end = (request.form.get("end_date") or "").strip()
    reason = (request.form.get("reason") or request.form.get("notes") or "").strip()

    if not start:
        start = date.today().isoformat()
    if not end:
        end = start

    # Prefer explicit technician_id from the form; fall back to session user id.
    tech_id = (request.form.get("technician_id") or "").strip() or None
    conn = get_database()
    cur = conn.cursor()

    if tech_id:
        cur.execute(
            "INSERT INTO time_off (technician_id, start_date, end_date, reason) VALUES (?, ?, ?, ?)",
            (tech_id, start, end, reason),
        )
    else:
        # Try user_id first; fallback to technician_id with the same value if schema uses technicians only.
        try:
            cur.execute(
                "INSERT INTO time_off (user_id, start_date, end_date, reason) VALUES (?, ?, ?, ?)",
                (user["user_id"], start, end, reason),
            )
        except Exception:
            cur.execute(
                "INSERT INTO time_off (technician_id, start_date, end_date, reason) VALUES (?, ?, ?, ?)",
                (user["user_id"], start, end, reason),
            )

    conn.commit()
    flash("Time off added.", "success")
    return redirect(request.referrer or url_for("calendar.index"))


@calendar_bp.route("/time_off/<int:time_off_id>/delete", methods=["POST"])
@login_required
def delete_time_off(time_off_id: int):
    """Remove a time-off entry. Allow admin/manager or owner to delete."""
    user = session["user"]
    is_admin = str(user.get("role", "")).lower() in {"admin", "manager"}

    conn = get_database()
    cur = conn.cursor()
    cur.execute("SELECT * FROM time_off WHERE id = ?", (time_off_id,))
    row = cur.fetchone()
    if not row:
        flash("Time off not found.", "error")
        return redirect(request.referrer or url_for("calendar.index"))

    # Detect owner column
    owner_id = None
    for key in ("user_id", "technician_id", "created_by", "owner_id"):
        if key in row.keys() and row[key] is not None:
            owner_id = row[key]
            break

    is_owner = owner_id == user.get("user_id")
    if not (is_admin or is_owner):
        flash("You don't have permission to remove this time off.", "error")
        return redirect(request.referrer or url_for("calendar.index"))

    cur.execute("DELETE FROM time_off WHERE id = ?", (time_off_id,))
    conn.commit()
    flash("Time off removed.", "success")
    return redirect(request.referrer or url_for("calendar.index"))


@calendar_bp.route("/lock/toggle", methods=["POST"], endpoint="toggle_lock")
@login_required
@role_required("admin", "manager", "technician")
def toggle_lock():
    """Toggle the lock status for a specific date."""
    selected_date = request.form.get("date")
    if not selected_date:
        flash("No date provided.", "error")
        return redirect(url_for("calendar.index"))

    user = session.get("user") or {}
    user_id = user.get("user_id") or user.get("id")
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
