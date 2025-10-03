from datetime import date, datetime

import zipcodes
from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from db import get_database
from utils.decorators import login_required, owner_or_role, role_required, write_guard
from utils.logger import setup_logger

job_bp = Blueprint("job", __name__)
logger = setup_logger()


def _current_user_id():
    u = getattr(g, "user", None)
    if isinstance(u, dict):
        uid = u.get("user_id") or u.get("id")
        if uid is not None:
            return int(uid)
    elif u is not None:
        uid = getattr(u, "id", None)
        if uid is not None:
            return int(uid)
    su = session.get("user") or {}
    uid = su.get("user_id") or session.get("user_id")
    return int(uid) if uid is not None else None


def _parse_date(s: str | None) -> date | None:
    """Parse a user-supplied date string into a `date`.

    Accepts ISO ``YYYY-MM-DD`` or US ``MM/DD/YYYY``.  Returns ``None`` for blank or unparsable values.  Does not raise.

    Args:
        s (str | None): Raw date value from a form.

    Returns:
        date | None: Parsed date, or ``None`` if parsing fails.
    """
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_technician(value: str | None, cur=None) -> tuple[int | None, int]:
    """Interpret the technician selector from the job form.

    The form value may be an integer ID (as a string), the sentinel ``"__BOTH__"`` to indicate a Two-Man Job, or blank.  If a DB cursor is provided, the ID is validated against the ``technicians`` table.

    Args:
        value (str | None): Form value (``"__BOTH__"``, ``""``, or int-like string).
        cur (optional): Optional SQLite cursor for existence check.

    Returns:
        tuple[int | None, int]: ``(technician_id, two_man)``. For ``"__BOTH__"`` returns ``(None, 1)``; for a valid technician ID returns ``(id, 0)``; otherwise ``(None, 0)``.
    """
    if value == "__BOTH__":
        return None, 1
    if value is None or str(value).strip() == "":
        return None, 0
    try:
        tid = int(value)
    except (TypeError, ValueError):
        return None, 0

    if cur is not None:
        ok = cur.execute("SELECT 1 FROM technicians WHERE id=?", (tid,)).fetchone()
        if not ok:
            return None, 0
    return tid, 0


def lookup_zipcode(zip_code: str) -> str | None:
    """Resolve a 5-digit ZIP code to a city name using ``zipcodes``.

    Args:
        zip_code (str): ZIP code as entered (whitespace allowed).

    Returns:
        str | None: City name if found; otherwise ``None``.
    """
    try:
        results = zipcodes.matching(str(zip_code).strip())
        if not results:
            return None
        city = results[0].get("city")
        return city.title() if city else None
    except Exception:
        return None


def normalize_hhmm(s: str | None) -> str | None:
    """Normalize a loose time input to ``HH:MM``.

    Accepts inputs like ``"9"``, ``"09"``, ``"9:30"``, ``"09:30"`` and returns canonical ``"09:00"`` or ``"09:30"``.  Returns ``None`` for blank/invalid.

    Args:
        s (str | None): Raw time string.

    Returns:
        str | None: Normalized time string, or ``None``.
    """
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    if s.isdigit():
        return f"{int(s):02d}:00"
    if ":" in s:
        h, m = s.split(":", 1)
        return f"{int(h):02d}:{int(m):02d}"
    return None


def derive_time_range(start_hhmm: str | None, end_hhmm: str | None) -> str | None:
    """Build a compact ``H-H`` label from start/end times.

    Intended for teh calendar's small badges.  Minuts are intentionally dropped (e.g., ``"09:30"`` - ``"14:00"`` => ``"9-14"``).  Returns ``None`` if either time is missing.

    Args:
        start_hhmm (str | None): Start time like ``"HH:MM"``.
        end_hhmm (str | None): End time like ``"HH:MM"``.

    Returns:
        str | None: A label like ``"9-14"`` or ``None``.
    """
    if not start_hhmm or not end_hhmm:
        return None
    sh, sm = map(int, start_hhmm.split(":"))
    eh, em = map(int, end_hhmm.split(":"))
    return f"{sh}-{eh}"


def _compose_job_payload(form, cur, start_date: date, end_date: date | None):
    # Times
    start_time = normalize_hhmm(form.get("start_time"))
    end_time = normalize_hhmm(form.get("end_time"))
    if start_time and end_time and end_time <= start_time:
        return None, "End time must be after start time."
    time_range = derive_time_range(start_time, end_time) or (
        form.get("time_range", "").strip() or "any"
    )

    # Technicians
    technician_raw = form.get("technician_id")
    technician_id, two_man = _parse_technician(technician_raw, cur)

    # REI fields
    rei_quantity_raw = (form.get("rei_quantity") or "").strip()
    rei_zip = (form.get("rei_zip") or "").strip()
    rei_city_free = (form.get("rei_city_name") or form.get("rei_city") or "").strip()
    if rei_city_free:
        rei_city_name = rei_city_free
    elif rei_zip.isdigit() and len(rei_zip) == 5:
        rei_city_name = lookup_zipcode(rei_zip)
    else:
        rei_city_name = None

        # REI Fields (ZIP or City or None; Quantity is required)
        # rei_quantity_raw = (form.get("rei_quantity") or "").strip()
        # rei_zip = (form.get("rei_quantity") or "").strip()
        # rei_city_free = (form.get("rei_city_name") or form.get("rei_city") or "").strip()
        # rei_city_name = None
        # if rei_city_free:
        #     rei_city_name = rei_city_free
        # elif rei_zip and rei_zip.isdigit() and len(rei_zip) == 5:
        #     rei_city_name = lookup_zipcode(rei_zip)
        #
        # REI Fields
        #   rei_quantity = form.get("rei_quantity")
        #  rei_zip = (form.get("rei_zip") or "").strip()
        # rei_city_name = None
        # if rei_zip and rei_zip.isdigit() and len(rei_zip) == 5:
        #    rei_city_name = lookup_zipcode(rei_zip)

    # Other Fields
    exclusion_subtype = (form.get("exclusion_subtype") or "").strip() or None
    fumigation_type = (form.get("fumigation_type") or "").strip() or None
    target_pest = (form.get("target_pest") or "").strip() or None
    custom_pest = (form.get("custom_pest") or "").strip() or None
    if (target_pest or "").lower() != "other":
        custom_pest = None
    elif custom_pest:
        target_pest = custom_pest

    # Core
    title = (form.get("title") or "").strip()
    job_type = (form.get("job_type") or "").strip().lower()
    if job_type == "custom":
        job_type = (form.get("custom_type") or "").strip()
    price = form.get("price")

    # End date normalization for REIs
    end_final = end_date

    # REI authoritative rules
    if job_type == "rei":
        title = "REIs"
        price = None
        end_final = start_date
        try:
            rei_quantity = int(rei_quantity_raw)
        except ValueError:
            return None, "Quantity required for REIs."
        if rei_quantity <= 0:
            return None, "Quantity required for REIs."
    else:
        if not title:
            return None, "Title is required."

    owner_id = _current_user_id()
    if owner_id is None:
        logger.warning(
            "add_job: no owner_id found in g/session; session.user=%r",
            session.get("user"),
        )
        abort(401)

    payload = {
        "title": title,
        "job_type": job_type,
        "price": price,
        "start_date": start_date.isoformat(),
        "end_date": end_final.isoformat() if end_final else None,
        "start_time": start_time,
        "end_time": end_time,
        "time_range": time_range,
        "notes": (form.get("notes", "") or ""),
        "technician_id": technician_id,
        "two_man": two_man,
        "rei_quantity": (
            int(rei_quantity_raw)
            if (job_type == "rei" and rei_quantity_raw.isdigit())
            else form.get("rei_quantity")
        ),
        "rei_zip": rei_zip,
        "rei_city_name": rei_city_name,
        "exclusion_subtype": exclusion_subtype,
        "fumigation_type": fumigation_type,
        "target_pest": target_pest,
        "custom_pest": custom_pest,
        "created_by": owner_id,
    }
    return payload, None


@job_bp.route("/add_job", methods=["GET", "POST"])
@login_required
@role_required("manager", "technician", "sales")
@write_guard
def add_job():
    """Create a new job (GET shows form, POST submits).

    Handles GET (render form) and POST (submit). Validates dates/times, supports REIs (ZIP -> city; ``end_date = start_date``), parses a single technician or ``"__BOTH__"`` for Two-Man, rejects locked days, inserts the job, and logs.

    Returns:
        Response: On success, redirect to ``calendar.index``.  On validation errors, redirect back to the form.  On GET, render the form.
    """

    conn = get_database()
    cur = conn.cursor()

    if request.method == "POST":
        # Dates (route-level)

        start_date_raw = request.form.get("start_date")
        if not start_date_raw:
            flash("Start date is required.", "error")
            return redirect(request.url)
        end_date_raw = request.form.get("end_date") or start_date_raw

        start_date = _parse_date(start_date_raw)
        end_date = _parse_date(end_date_raw) if end_date_raw else None
        if not start_date:
            flash("Start date is required.", "error")
            return redirect(request.url)

        # Validate/normalize

        payload, err = _compose_job_payload(request.form, cur, start_date, end_date)
        if err:
            flash(err, "error")
            return redirect(
                url_for("calendar.day_view", selected_date=start_date.isoformat())
            )

        # Locks/auth
        cur.execute("SELECT 1 FROM locks WHERE date = ?", (payload["start_date"],))
        if cur.fetchone():
            flash("Date is locked.  Cannot add job.", "error")
            return redirect(
                url_for("calendar.day_view", selected_date=payload["start_date"])
            )

        uid = session.get("user", {}).get("user_id")
        if not cur.execute("SELECT 1 FROM users WHERE id = ?", (uid,)).fetchone():
            session.clear()
            flash("Your session has expired.  Please log in again.", "error")
            return redirect(url_for("auth.login"))

        # Insert

        cur.execute(
            """
            INSERT INTO jobs (
                title, job_type, price, start_date, end_date,
                start_time, end_time, time_range, notes,
                created_by, technician_id, two_man,
                rei_quantity, rei_zip, rei_city_name,
                exclusion_subtype,
                fumigation_type, target_pest, custom_pest
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                payload["title"],
                payload["job_type"],
                payload["price"],
                payload["start_date"],
                payload["end_date"],
                payload["start_time"],
                payload["end_time"],
                payload["time_range"],
                payload["notes"],
                payload["created_by"],
                payload["technician_id"],
                payload["two_man"],
                payload["rei_quantity"],
                payload["rei_zip"],
                payload["rei_city_name"],
                payload["exclusion_subtype"],
                payload["fumigation_type"],
                payload["target_pest"],
                payload["custom_pest"],
            ),
        )
        conn.commit()
        logger.info(
            f"Job added by user ID {uid}: {payload['job_type']} from {payload['start_date']} to {payload['end_date']} @ {payload['time_range']}"
        )
        return redirect(url_for("calendar.index"))

    # GET: render form
    cur.execute("SELECT * FROM technicians")
    technicians = cur.fetchall()
    return render_template(
        "job_form.html", date=None, technicians=technicians, hide_date_fields=False
    )


@job_bp.route("/add_job/<date>", methods=["GET", "POST"])
@login_required
@role_required("manager", "technician", "sales")
@write_guard
def add_job_for_date(date):
    """Create a job for a specific day.

    Uses the URL date (``YYYY-MM-DD``) as both ``start_date`` and ``end_date``.  Applies the same validation rules as ``add_job`` and rejects locked days.

    Args:
        date (str): ISO date from the route segment (``YYYY-MM-DD``).

    Returns:
        Response: GET renders the form with date fields prefilled/hidden.  POST redirects to ``calendar.day_view`` on success; otherwise re-renders with errors.
    """
    if request.method == "POST":

        owner_id = _current_user_id()
        if not owner_id:
            abort(401)

        conn = get_database()
        cur = conn.cursor()

        try:
            sd = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date.", "error")
            return redirect(url_for("calendar.index"))
        ed = sd

        payload, err = _compose_job_payload(request.form, cur, sd, ed)
        if err:
            flash(err, "error")
            return redirect(url_for("calendar.day_view", selected_date=date))

        # Locks
        cur.execute("SELECT 1 FROM locks WHERE date = ?", (payload["start_date"],))
        if cur.fetchone():
            flash("Date is locked. Cannot add job.", "error")
            return redirect(url_for("calendar.day_view", selected_date=date))
        cur.execute(
            """
            INSERT INTO jobs (
                title, job_type, price, start_date, end_date, start_time, end_time, time_range, notes, technician_id, two_man, created_by, rei_quantity, rei_zip, rei_city_name, exclusion_subtype, fumigation_type, target_pest, custom_pest) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                payload["title"],
                payload["job_type"],
                payload["price"],
                payload["start_date"],
                payload["end_date"],
                payload["start_time"],
                payload["end_time"],
                payload["time_range"],
                payload["notes"],
                payload["technician_id"],
                payload["two_man"],
                payload["created_by"],
                payload["rei_quantity"],
                payload["rei_zip"],
                payload["rei_city_name"],
                payload["exclusion_subtype"],
                payload["fumigation_type"],
                payload["target_pest"],
                payload["custom_pest"],
            ),
        )
        conn.commit()
        logger.info(
            f"Job added by user ID {owner_id}: {payload['job_type']} on {date} @ {payload['time_range']}"
        )
        return redirect(url_for("calendar.day_view", selected_date=date))

    if request.method == "GET":
        conn = get_database()
        cur = conn.cursor()
        cur.execute("SELECT * FROM technicians")
        technicians = cur.fetchall()

        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        return render_template(
            "job_form.html",
            date=parsed_date,
            technicians=technicians,
            hide_date_fields=True,
        )


@job_bp.route("/move_job/<int:job_id>", methods=["GET", "POST"])
@login_required
@owner_or_role()
@write_guard
def move_job(job_id: int):
    conn = get_database()
    cur = conn.cursor()
    job = cur.execute(
        "SELECT id, start_date, end_date FROM jobs WHERE id = ?", (job_id,)
    ).fetchone()
    if not job:
        return "Job not found", 404

    if request.method == "GET":
        qs = (request.args.get("new_date") or "").strip()
        if qs:
            new_start = qs
        else:
            return render_template(
                "move_job.html",
                job=job,
                next=request.args.get("next") or request.referrer,
            )
    else:
        new_start = (request.form.get("new_date") or "").strip()
        if not new_start:
            flash("Pick a new date.", "error")
            return redirect(request.referrer or url_for("calendar.index"))

    # compute duration and update … (your existing logic)
    return redirect(
        request.form.get("next")
        or request.args.get("next")
        or url_for("calendar.day_view", selected_date=new_start)
    )


@job_bp.route("/delete_job/<int:job_id>", methods=["POST"])
@login_required
@owner_or_role()
# @role_required("manager", "sales")
@write_guard
def delete_job(job_id):
    """Delete a job permanently.

    Removes the job from the ``jobs`` table and logs the action.

    Args:
        job_id (int): Identifier of the job to delete.

    Returns:
        Response: Redirect to the referrer or ``calendar.index``.

    """
    if "user" not in session:
        return redirect(url_for("auth.login"))
    conn = get_database()
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    logger.info(f"Job ID {job_id} deleted by user ID {session['user']['user_id']}")
    return redirect(request.referrer or url_for("calendar.index"))


@job_bp.route("/edit_job/<int:job_id>", methods=["GET", "POST"])
@login_required
@owner_or_role()
# @role_required("manager", "sales")
@write_guard
def edit_job(job_id):
    """Edit an existing job.

    On POST, validates and normalizes dates/times (end must be >= start), enforces title for non-REI jobs.parses technician or Two-Man selection via ``_parse_technicians``, updates price/notes/fumigation/target pest, and audit columns.

    Args:
        job_id (int): Identifier of the job to edit.

    Returns:
        Response: On success, redirect to ``calendar.index``.  On validation errors, re-render ``edit_job.html`` with the current job.
    """
    if "user" not in session:
        return redirect(url_for("auth.login"))

    conn = get_database()
    cur = conn.cursor()
    if request.method == "POST":
        fumigation_type = request.form.get("fumigation_type")
        target_pest = request.form.get("target_pest")
        custom_pest = request.form.get("custom_pest")
        start_time_raw = request.form.get("start_time")
        end_time_raw = request.form.get("end_time")

        start_time = normalize_hhmm(start_time_raw)
        end_time = normalize_hhmm(end_time_raw)

        if start_time and end_time and end_time <= start_time:
            flash("End time must be after start time.", "error")
            return render_template(
                "edit_job.html",
                job=cur.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone(),
            )

        time_range = derive_time_range(start_time, end_time) or (
            request.form.get("time_range", "").strip() or "any"
        )

        if custom_pest:
            target_pest = custom_pest.strip()

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
        job_type = (
            (request.form.get("job_type") or request.form.get("type") or "")
            .strip()
            .lower()
        )
        if job_type == "custom":
            job_type = (request.form.get("custom_type") or "").strip()
        if job_type == "rei":
            title = "REIs"
            request_price = None
            ed = sd
        else:
            if not title:
                flash("Title is required.", "error")
                return render_template(
                    "edit_job.html",
                    job=cur.execute(
                        "SELECT * FROM jobs WHERE id = ?", (job_id,)
                    ).fetchone(),
                )
            request_price = request.form.get("price")

        technician_raw = request.form.get("technician_id")
        technician_id, two_man = _parse_technician(technician_raw, cur)

        cur.execute(
            """
            UPDATE jobs
                SET title = ?,
                    job_type = ?,
                    price = ?,
                    start_date = ?,
                    end_date = ?,
                    start_time = ?,
                    end_time = ?,
                    time_range = ?,
                    notes = ?,
                    fumigation_type = ?,
                    target_pest = ?,
                    technician_id = ?,
                    two_man = ?,
                    last_modified = CURRENT_TIMESTAMP,
                    last_modified_by = ?
            WHERE id = ?
            """,
            (
                title,
                job_type,
                request_price,
                sd.isoformat(),
                ed.isoformat() if ed else None,
                start_time,
                end_time,
                time_range,
                request.form.get("notes", ""),
                fumigation_type,
                target_pest,
                technician_id,
                two_man,
                session["user"]["user_id"],
                job_id,
            ),
        )

        conn.commit()
        logger.info(f"Job ID {job_id} edited by user ID {session['user']['user_id']}")
        return redirect(url_for("calendar.index"))

    job = cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return render_template("edit_job.html", job=job)


@job_bp.post("/timeoff/add")
@login_required
@role_required("manager", "technician")
@write_guard
def timeoff_add():
    conn = get_database()
    cur = conn.cursor()
    uid = session.get("user", {}).get("user_id")
    role = cur.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
    role_name = (role["role"] if role else "").lower()

    tech_id_raw = request.form.get("technician_id")
    tech_id = int(tech_id_raw) if tech_id_raw and tech_id_raw.isdigit() else uid
    reason = request.form.get("reason")

    if role_name not in ("manager", "admin"):
        tech_id = uid

    d = (request.form.get("date") or "").strip()
    if not d:
        flash("Invalid date for time off.", "error")
        return redirect(request.referrer or url_for("calendar.index"))

    cur.execute(
        "INSERT INTO time_off (technician_id, date, reason, created_at, created_by) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)",
        (tech_id, d, reason, uid),
    )
    conn.commit()
    logger.info(f"time_off added for tech {tech_id} by user {uid} on {d}")
    return redirect(request.referrer or url_for("calendar.index"))


@job_bp.post("/timeoff/delete/<int:timeoff_id>", endpoint="timeoff_delete")
@login_required
@owner_or_role()
# @role_required("admin", "manager", "technician")
@write_guard
def timeoff_delete(timeoff_id: int):
    conn = get_database()
    cur = conn.cursor()

    toff = cur.execute(
        """
        SELECT t.id,
                t.technician_id,
                t.start_date,
                t.end_date,
                tech.name AS tech_name
        FROM time_off AS t
        LEFT JOIN technicians AS tech ON tech.id = t.technician_id
        WHERE t.id = ?
    """,
        (timeoff_id,),
    ).fetchone()

    if not toff:
        flash("Time off entry not found.", "error")
        return redirect(request.referrer or url_for("calendar.index"))

    # session
    user = session.get("user") or {}
    uid = user.get("user_id") or user.get("id")
    if not uid:
        flash("You must be logged in.", "error")
        return redirect(url_for("auth.login"))

    urow = cur.execute(
        "SELECT id, role, first_name, last_name FROM users WHERE id = ?", (uid,)
    ).fetchone()
    if not urow:
        flash("Session user not found.", "error")
        return redirect(request.referrer or url_for("calendar.index"))

    role = (urow["role"] or "").lower()
    allowed = False

    if role in ("admin", "manager"):
        allowed = True
    elif role in ("technician", "tech"):
        full_name = f"{(urow['first_name'] or '').strip()} {(urow['last_name'] or '').strip()}".strip()
        match = cur.execute(
            " SELECT id FROM technicians WHERE lower(trim(name)) = lower(trim(?))",
            (full_name,),
        ).fetchone()
        if match and match["id"] == toff["technician_id"]:
            allowed = True

    if not allowed:
        flash("Not authorized to remove this time off.", "error")
        target_day = toff["start_date"]
        return redirect(url_for("calendar.day_view", selected_date=target_day))

    cur.execute("DELETE FROM time_off WHERE id = ?", (timeoff_id,))
    conn.commit()
    flash("Time off is removed.", "success")
    target_day = toff["start_date"]
    return redirect(url_for("calendar.day_view", selected_date=target_day))
