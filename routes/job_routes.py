from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime, date
from ..utils.decorators import login_required, role_required
from ..db import get_database
from ..logger import setup_logger
from functools import wraps
from datetime import datetime
import zipcodes

job_bp = Blueprint("job", __name__)
logger = setup_logger()


def _parse_date(s: str | None) -> date | None:
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def lookup_zipcode(zip: str) -> str | None:
    try:
        results = zipcodes.matching(str(zip).strip())
        if not results:
            return None
        return results[0].get("city")
    except Exception:
        return None


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@job_bp.route("/add_job", methods=["GET", "POST"])
@login_required
def add_job():
    if request.method == "POST":
        start_date_raw = request.form.get("start_date")
        rei_city = request.form.get("rei_city")
        rei_city_name = lookup_zipcode(rei_city) if rei_city else None
        if not start_date_raw:
            flash("Start date is required.")
            return redirect(request.url)

        # BUG-1018: correct fallback and validate dates
        end_date_raw = request.form.get("end_date") or start_date_raw
        sd = _parse_date(start_date_raw)
        ed = _parse_date(end_date_raw) if end_date_raw else None
        if not sd:
            flash("Start date is invalid.", "error")
            return redirect(request.url)
        start_date = sd.isoformat()
        end_date = ed.isoformat() if ed else None

        title = (request.form.get("title") or "").strip()
        job_type = request.form["type"]

        if job_type == "reis":
            title = ""
            end_date = start_date
        if job_type == "custom":
            job_type = request.form.get("custom_type", "").strip()

        # BUG-1009: require non-empty title for non-REI jobs
        if job_type != "reis" and not title:
            flash("Title is required.", "error")
            return redirect(request.url)

        price = request.form["price"]
        time_range = request.form.get("time_range", "").strip() or "any"
        notes = request.form.get("notes", "")

        conn = get_database()
        cur = conn.cursor()

        uid = session.get("user", {}).get("user_id")
        row = cur.execute("SELECT id FROM users WHERE id=?", (uid,)).fetchone()
        if not row:
            session.clear()
            flash("Your session has expired.  Please log in again.", "error")
            return redirect(url_for("auth.login"))
        created_by = uid
        rei_quantity = request.form.get("rei_quantity")
        rei_city = request.form.get("rei_city")
        exclusion_subtype = request.form.get("exclusion_subtype")
        technician_id = request.form.get("technician_id") or None
        if technician_id == "":
            technician_id = None
        if technician_id is not None:
            if not cur.execute(
                "SELECT 1 FROM technicians WHERE id=?", (technician_id,)
            ).fetchone():
                technician_id = None

        fumigation_type = request.form.get("fumigation_type")
        target_pest = request.form.get("target_pest")
        custom_pest = request.form.get("custom_pest")

        if custom_pest:
            target_pest = custom_pest.strip()

        conn = get_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM locks WHERE date = ?", (start_date,))
        if cursor.fetchone():
            return "Date is locked. Cannot add job.", 403

        cursor.execute(
            """INSERT INTO jobs (
            title, job_type, price, start_date, end_date, time_range, notes,
            created_by, technician_id, rei_qty, rei_city, rei_city_name, exclusion_subtype, fumigation_type, target_pest, custom_pest)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title,
                job_type,
                price,
                start_date,
                end_date,
                time_range,
                notes,
                created_by,
                technician_id,
                rei_quantity,
                rei_city,
                rei_city_name,
                exclusion_subtype,
                fumigation_type,
                target_pest,
                custom_pest,
            ),
        )
        conn.commit()
        logger.info(
            f"Job added by user ID {created_by}: {job_type} from {start_date} to {end_date} at {time_range}"
        )
        return redirect(url_for("calendar.index"))
    start_date = None
    connection = get_database()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM technicians")
    technicians = cursor.fetchall()

    return render_template(
        "job_form.html",
        date=start_date,
        technicians=technicians,
        hide_date_fields=False,
    )


@job_bp.route("/add_job/<date>", methods=["GET", "POST"])
@login_required
def add_job_for_date(date):
    if request.method == "POST":

        start_date = end_date = date

        title = request.form["title"]
        job_type = request.form["type"]
        if job_type == "custom":
            job_type = request.form.get("custom_type", "").strip()
        price = request.form["price"]
        time_range = request.form.get("time_range", "").strip() or "any"
        notes = request.form.get("notes", "")
        created_by = session["user"]["user_id"]
        rei_quantity = request.form.get("rei_quantity")
        rei_city = request.form.get("rei_city")
        rei_city_name = request.form.get("rei_city_name")
        exclusion_subtype = request.form.get("exclusion_subtype")
        technician_id = request.form.get("technician_id") or None
        if technician_id == "":
            technician_id = None

        conn = get_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM locks WHERE date = ?", (date,))
        if cursor.fetchone():
            return "Date is locked. Cannot add job.", 403

        cursor.execute(
            """INSERT INTO jobs (title, job_type, price, start_date, end_date, time_range, notes, technician_id, created_by, rei_qty, rei_city, rei_city_name, exclusion_subtype)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title,
                job_type,
                price,
                start_date,
                end_date,
                time_range,
                notes,
                technician_id,
                created_by,
                rei_quantity,
                rei_city,
                rei_city_name,
                exclusion_subtype,
            ),
        )
        conn.commit()
        logger.info(
            f"Job added by user ID {created_by}: {job_type} from {start_date} to {end_date} at {time_range}"
        )
        return redirect(url_for("calendar.day_view", selected_date=date))

    # ✅ This block only runs on GET
    connection = get_database()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM technicians")
    technicians = cursor.fetchall()

    parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
    return render_template(
        "job_form.html",
        date=parsed_date,
        technicians=technicians,
        hide_date_fields=True,
    )


@job_bp.route("/move_job/<int:job_id>", methods=["POST"])
@login_required
def move_job(job_id):
    new_start = request.form["new_date"]
    conn = get_database()
    cur = conn.cursor()

    # get current job duration
    job = cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        return "Job not found", 404

    old_start = datetime.strptime(job["start_date"], "%Y-%m-%d").date()
    if job["end_date"]:
        old_end = datetime.strptime(job["end_date"], "%Y-%m-%d").date()
    else:
        old_end = old_start
    duration = old_end - old_start

    new_start_dt = datetime.strptime(new_start, "%Y-%m-%d").date()
    new_end_dt = new_start_dt + duration

    cur.execute(
        """
                UPDATE jobs
                SET start_date = ?, end_date = ?,
                last_modified = CURRENT_TIMESTAMP,
                last_modified_by = ?
            WHERE id = ?
        """,
        (
            new_start_dt.isoformat(),
            new_end_dt.isoformat(),
            session["user"]["user_id"],
            job_id,
        ),
    )

    conn.commit()
    logger.info(
        f"Job ID {job_id} moved by user ID {session['user']['user_id']} to {new_start_dt}"
    )
    return redirect(request.referrer or url_for("calendar.index"))


@job_bp.route("/delete_job/<int:job_id>", methods=["POST"])
@login_required
def delete_job(job_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))
    conn = get_database()
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    logger.info(f"Job ID {job_id} deleted by user ID {session['user']['user_id']}")
    return redirect(request.referrer or url_for("calendar.index"))


@job_bp.route("/edit_job/<int:job_id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager", "sales")
def edit_job(job_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))

    conn = get_database()
    cur = conn.cursor()
    if request.method == "POST":
        fumigation_type = request.form.get("fumigation_type")
        target_pest = request.form.get("target_pest")
        custom_pest = request.form.get("custom_pest")

        if custom_pest:
            target_pest = custom_pest.strip()

        cur.execute(
            """UPDATE jobs SET title = ?, type = ?, price = ?, time_range = ?, notes = ?, fumigation_type = ?, target_pest = ?, last_modified = CURRENT_TIMESTAMP, last_modified_by = ? WHERE id = ?""",
            (
                request.form["title"],
                request.form["type"],
                request.form["price"],
                request.form["time_range"],
                request.form["notes"],
                fumigation_type,
                target_pest,
                session["user"]["user_id"],
                job_id,
            ),
        )
        # BUG-1018: validate and normalize dates on edit
        start_date_raw = request.form.get("start_date")
        end_date_raw = request.form.get("end_date") or start_date_raw
        sd = _parse_date(start_date_raw)
        ed = _parse_date(end_date_raw) if end_date_raw else None
        if not sd:
            flash("Start date is invalid.", "error")
            return render_template(
                "edit_job.html",
                job=cur.execute(
                    "SELECT * FROM jobs WHERE id = ?", (job_id,)
                ).fetchone(),
            )
        if ed and ed < sd:
            flash("End date cannot be before start date.", "error")
            return render_template(
                "edit_job.html",
                job=cur.execute(
                    "SELECT * FROM jobs WHERE id = ?", (job_id,)
                ).fetchone(),
            )

        title = (request.form.get("title") or "").strip()
        job_type = request.form.get("type")
        if job_type == "custom":
            job_type = (request.form.get("custom_type") or "").strip()
        if job_type != "reis" and not title:
            flash("Title is required.", "error")
            return render_template(
                "edit_job.html",
                job=cur.execute(
                    "SELECT * FROM jobs WHERE id = ?", (job_id,)
                ).fetchone(),
            )

        cur.execute(
            """
            UPDATE jobs
                SET title = ?,
                    job_type = ?,
                    price = ?,
                    start_date = ?,
                    end_date = ?,
                    time_range = ?,
                    notes = ?,
                    fumigation_type = ?,
                    target_pest = ?,
                    last_modified = CURRENT_TIMESTAMP,
                    last_modified_by = ?,
            WHERE id = ?
            """,
            (
                title,
                job_type,
                request.form["price"],
                sd.isoformat(),
                ed.isoformat() if ed else None,
                request.form.get("time_range", "").strip() or "any",
                request.form.get("notes", ""),
                fumigation_type,
                target_pest,
                session["user"]["user_id"],
                job_id,
            ),
        )

        conn.commit()
        logger.info(f"Job ID {job_id} edited by user ID {session['user']['user_id']}")
        return redirect(url_for("calendar.index"))

    job = cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return render_template("edit_job.html", job=job)
