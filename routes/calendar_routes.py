from datetime import date, datetime, timedelta
from calendar import Calendar, month_name
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..db import get_database
from ..logger import setup_logger

calendar_bp = Blueprint("calendar", __name__)
log = setup_logger()

def _month_weeks(year: int, month: int, firstweekday: int=6):
    cal = Calendar(firstweekday=firstweekday)
    days = list(cal.itermonthdates(year, month))
    return [days[i:i+7] for i in range(0, len(days), 7)]

def _expand_multi_day(sd_str: str, ed_str: str | None):
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

    weeks = _month_weeks(year, month)

    prev_month, prev_year = (12, year - 1) if month == 1 else (month -1, year)
    next_month, next_year = (1, year+1) if month == 12 else (month + 1, year)

    conn = get_database()
    cur = conn.cursor()

    cur.execute("SELECT date FROM locks")
    locks = {row["date"] for row in cur.fetchall()}

    jobs_by_date = {}
    time_off_by_date = {}

    cur.execute(
        """
        SELECT j.*,
            j.job_type AS type,
            j.rei_qty AS rei_quantity,
            t.name AS technician_name
        FROM jobs j
        LEFT JOIN technicians t ON t.id = j.technician_id
        """
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
            time_off_by_date.setdefault(d.isoformat(), []).append(row["technician_name"])

    conn.close()

    holidays = {}

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
        holidays=holidays,
        jobs_by_date=jobs_by_date,
        time_off_by_date=time_off_by_date,
        today=today,
    )

@calendar_bp.route("/day/<selected_date>", endpoint="day_view")
def day_view(selected_date: str):
    try:
        dt = datetime.fromisoformat(selected_date).date()
    except Exception:
        return redirect(url_for("calendar.index"))

    conn = get_database()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM locks WHERE date = ?", (selected_date,))
    locked = cur.fetchone() is not None

    cur.execute(
        """
        SELECT j.*,
                j.job_type AS type,
                j.rei_qty AS rei_quantity,
                t.name AS technician_name
        FROM jobs j
        LEFT JOIN technicians t ON t.id = j.technician_id
        WHERE j.start_date <= ? AND (j.end_date IS NULL OR j.end_date >= ?)
        """,
        (selected_date, selected_date),
    )
    jobs = cur.fetchall()

    conn.close()
    return render_template("day.html", selected_date=dt, locked=locked, jobs=jobs)

@calendar_bp.route("/timeoff/add", methods=["GET", "POST"], endpoint="add_time_off")
def add_time_off():
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

        cur.execute("INSERT INTO time_off (technician_id, start_date, end_date, reason) VALUES (?, ?, ?, ?)", (technician_id, start_date, end_date, reason),)
        conn.commit()
        flash("Time off added.", "success")
        return redirect(url_for("calendar.index"))

    cur.execute("SELECT id, name FROM technicians ORDER BY name")
    technicians = cur.fetchall()
    conn.close()
    return render_template("add_time_off.html", technicians=technicians)

@calendar_bp.route("/lock/toggle", methods=["POST"], endpoint="toggle_lock")
def toggle_lock():
    selected_date = request.form.get("date")
    if not selected_date:
        flash("No date provided.", "error")
        return redirect(url_for("calendar.index"))

    user = session.get('user')
    user_id = user["id"] if isinstance(user, dict) and "id" in user else None

    conn = get_database()
    cur = conn.cursor()

    cur.execute("SELECT id FROM locks WHERE date = ?", (selected_date,))
    row = cur.fetchone()

    if row:
        cur.execute("DELETE FROM locks WHERE date = ?", (selected_date,))
        conn.commit()
        flash(f'Unlocked {selected_date}.', "success")
    else:
        cur.execute("INSERT INTO locks (date, locked_by) VALUES (?, ?)", (selected_date, user_id),)
        conn.commit()
        flash(f"Locked {selected_date}.", "success")

    conn.close()
    return redirect(url_for("calendar.day_view", selected_date=selected_date))