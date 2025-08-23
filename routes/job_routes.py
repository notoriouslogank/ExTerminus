from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response,
)
from functools import wraps
from datetime import datetime, date
from ..utils.decorators import login_required, role_required
from ..db import get_database
from ..utils.logger import setup_logger
from ..utils.holidays_util import is_holiday
import zipcodes

job_bp = Blueprint("job", __name__)
logger = setup_logger()


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
        return results[0].get("city")
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

    # REI Fields
    rei_quantity = form.get("rei_quantity")
    rei_zip = (form.get("rei_zip") or "").strip()
    rei_city_name = None
    if rei_zip and rei_zip.isdigit() and len(rei_zip) == 5:
        rei_city_name = lookup_zipcode(rei_zip)

    # Other Fields
    exclusion_subtype = form.get("exclusion_subtype")
    fumigation_type = form.get("fumigation_type")
    target_pest = form.get("target_pest")
    custom_pest = form.get("custom_pest")
    if custom_pest:
        target_pest = custom_pest.strip()

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
        missing = []
        if not (rei_quantity and str(rei_quantity).strip()):
            missing.append("REI quantity")
        if not (rei_zip and str(rei_zip).strip()):
            missing.append("REI city name")
        if not (rei_city_name and str(rei_city_name).strip()):
            missing.append("REI city name")
        if missing:
            return None, f"Missing required REI field(s): {', '.join(missing)}."
    else:
        if not title:
            return None, "Title is required."

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
        "rei_quantity": rei_quantity,
        "rei_zip": rei_zip,
        "rei_city_name": rei_city_name,
        "exclusion_subtype": exclusion_subtype,
        "fumigation_type": fumigation_type,
        "target_pest": target_pest,
        "custom_pest": custom_pest,
    }
    return payload, None


@job_bp.route("/add_job", methods=["GET", "POST"])
@login_required
@role_required("manager", "technician", "sales")
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
                uid,
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
    # conn = get_database()
    # cur = conn.cursor()

    # if request.method == "POST":
    #     start_date_raw = request.form.get("start_date")
    #     rei_quantity = request.form.get("rei_quantity")
    #     rei_zip = (request.form.get("rei_zip") or "").strip()
    #     rei_city_name = None
    #     if rei_zip and rei_zip.isdigit() and len(rei_zip) == 5:
    #         try:
    #             match = zipcodes.matching(rei_zip)
    #             rei_city_name = match[0]["city"] if match else None
    #         except Exception:
    #             rei_city_name = None

    #     if not start_date_raw:
    #         flash("Start date is required.", "error")
    #         return redirect(request.url)

    #     # Dates

    #     end_date_raw = request.form.get("end_date") or start_date_raw
    #     sd = _parse_date(start_date_raw)
    #     ed = _parse_date(end_date_raw) if end_date_raw else None
    #     if not sd:
    #         flash("Start date is invalid.", "error")
    #         return redirect(request.url)
    #     start_date = sd.isoformat()
    #     end_date = ed.isoformat() if ed else None

    #     # Times
    #     start_time_raw = request.form.get("start_time")
    #     end_time_raw = request.form.get("end_time")
    #     start_time = normalize_hhmm(start_time_raw)
    #     end_time = normalize_hhmm(end_time_raw)
    #     if start_time and end_time and end_time <= start_time:
    #         flash("End time must be after start time.", "error")
    #         return redirect(url_for("calendar.day_view", selected_date=start_date))

    #     time_range = derive_time_range(start_time, end_time) or (
    #         request.form.get("time_range", "").strip() or "any"
    #     )

    #     # Job Fields
    #     title = (request.form.get("title") or "").strip()
    #     job_type = (request.form.get("job_type") or "").strip().lower()
    #     # Normalize Custom Type
    #     if job_type == "custom":
    #         job_type = (request.form.get("custom_type") or "").strip()
    #     # Enforce REI semantics
    #     if job_type == "rei":
    #         title = "REIs"
    #         price = None
    #         end_date = start_date
    #         missing = []
    #         if not (rei_quantity and str(rei_quantity).strip()):
    #             missing.append("REI quantity")
    #         if not (rei_zip and str(rei_zip).strip()):
    #             missing.append("REI ZIP")
    #         if not (rei_city_name and str(rei_city_name).strip()):
    #             missing.append("REI city name")
    #         if missing:
    #             flash(f"Missing required REI field(s): {', '.join(missing)}.", "error")
    #             return redirect(url_for("calendar.day_view", selected_date=start_date))
    #     else:
    #         # Non-REI jobs require a title and can have a price
    #         if not title:
    #             flash("Title is required.", "error")
    #             return redirect(request.url)
    #         price = request.form.get("price")
    #         notes = request.form.get("notes", "")

    #     uid = session.get("user", {}).get("user_id")
    #     row = cur.execute("SELECT id FROM users WHERE id=?", (uid,)).fetchone()
    #     if not row:
    #         session.clear()
    #         flash("Your session has expired.  Please log in again.", "error")
    #         return redirect(url_for("auth.login"))
    #     created_by = uid

    #     exclusion_subtype = request.form.get("exclusion_subtype")
    #     technician_raw = request.form.get("technician_id")
    #     technician_id, two_man = _parse_technician(technician_raw, cur)

    #     fumigation_type = request.form.get("fumigation_type")
    #     target_pest = request.form.get("target_pest")
    #     custom_pest = request.form.get("custom_pest")
    #     if custom_pest:
    #         target_pest = custom_pest.strip()

    #     cur.execute("SELECT * FROM locks WHERE date = ?", (start_date,))
    #     if cur.fetchone():
    #         flash("Date is locked. Cannot add job.", "error")
    #         return redirect(url_for("calendar.day_view", selected_date=start_date))

    #     cur.execute(
    #         """INSERT INTO jobs (
    #         title, job_type, price, start_date, end_date, start_time, end_time, time_range, notes,
    #         created_by, technician_id, two_man, rei_quantity, rei_zip, rei_city_name, exclusion_type, exclusion_subtype, fumigation_type, target_pest, custom_pest)
    #            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    #         (
    #             title,
    #             job_type,
    #             price,
    #             start_date,
    #             end_date,
    #             start_time,
    #             end_time,
    #             time_range,
    #             notes,
    #             created_by,
    #             technician_id,
    #             two_man,
    #             rei_quantity,
    #             rei_zip,
    #             rei_city_name,
    #             request.form.get("exclusion_type"),
    #             exclusion_subtype,
    #             fumigation_type,
    #             target_pest,
    #             custom_pest,
    #         ),
    #     )
    #     conn.commit()
    #     logger.info(
    #         f"Job added by user ID {created_by}: {job_type} from {start_date} to {end_date} at {time_range}"
    #     )
    #     return redirect(url_for("calendar.index"))
    # start_date = None
    # cur.execute("SELECT * FROM technicians")
    # technicians = cur.fetchall()

    # return render_template(
    #     "job_form.html",
    #     date=start_date,
    #     technicians=technicians,
    #     hide_date_fields=False,
    # )


@job_bp.route("/add_job/<date>", methods=["GET", "POST"])
@login_required
@role_required("manager", "technician", "sales")
def add_job_for_date(date):
    """Create a job for a specific day.

    Uses the URL date (``YYYY-MM-DD``) as both ``start_date`` and ``end_date``.  Applies the same validation rules as ``add_job`` and rejects locked days.

    Args:
        date (str): ISO date from the route segment (``YYYY-MM-DD``).

    Returns:
        Response: GET renders the form with date fields prefilled/hidden.  POST redirects to ``calendar.day_view`` on success; otherwise re-renders with errors.
    """
    if request.method == "POST":
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

        uid = session.get("user", {}).get("user_id")

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
                uid,
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
            f"Job added by user ID {uid}: {payload['job_type']} on {date} @ {payload['time_range']}"
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
    # if request.method == "POST":
    #     conn = get_database()
    #     cursor = conn.cursor()

    #     start_date = end_date = date

    #     title = (request.form.get("title") or "").strip()
    #     job_type = (request.form.get("job_type") or "").strip().lower()
    #     if job_type == "custom":
    #         job_type = (request.form.get("custom_type") or "").strip()
    #     if job_type == "rei":
    #         title = "REIs"
    #         price = None
    #         missing = []
    #         if not (rei_quantity and str(rei_quantity).strip()):
    #             missing.append("REI quantity")
    #         if not (rei_zip and str(rei_zip).strip()):
    #             missing.append("REI ZIP")
    #         if missing:
    #             flash(f"Missing required REI field(s): {', '.join(missing)}.", "error")
    #             return redirect(url_for("calendar.day_view", selected_date=date))

    #     # title = request.form["title"]
    #     # job_type = request.form["type"]
    #     # if job_type == "custom":
    #     #    job_type = request.form.get("custom_type", "").strip()
    #     # price = request.form["price"]

    #     # time fields
    #     start_time_raw = request.form.get("start_time")
    #     end_time_raw = request.form.get("end_time")

    #     start_time = normalize_hhmm(start_time_raw)
    #     end_time = normalize_hhmm(end_time_raw)

    #     if start_time and end_time and end_time <= start_time:
    #         flash("End time must be after start time.", "error")
    #         return redirect(request.url)

    #     time_range = derive_time_range(start_time, end_time) or (
    #         request.form.get("time_range", "").strip() or "any"
    #     )

    #     notes = request.form.get("notes", "")
    #     created_by = session["user"]["user_id"]
    #     rei_quantity = request.form.get("rei_quantity")
    #     rei_zip = (request.form.get("rei_zip") or "").strip()
    #     rei_city_name = None
    #     if rei_zip and rei_zip.isdigit() and len(rei_zip) == 5:
    #         try:
    #             match = zipcodes.matching(rei_zip)
    #             rei_city_name = match[0]["city"] if match else None
    #         except Exception:
    #             rei_city_name = None
    #     exclusion_subtype = request.form.get("exclusion_subtype")
    #     technician_raw = request.form.get("technician_id")
    #     technician_id, two_man = _parse_technician(technician_raw, cursor)
    #     fumigation_type = request.form.get("fumigation_type")
    #     target_pest = request.form.get("target_pest")
    #     custom_pest = request.form.get("custom_pest")
    #     if custom_pest:
    #         target_pest = custom_pest.strip()

    #     cursor.execute("SELECT * FROM locks WHERE date = ?", (date,))
    #     if cursor.fetchone():
    #         flash("Date is locked. Cannot add job.", "error")
    #         return redirect(url_for("calendar.day_view", selected_date=date))

    #     cursor.execute(
    #         """INSERT INTO jobs (title, job_type, price, start_date, end_date, start_time, end_time, time_range, notes, technician_id, two_man, created_by, rei_quantity, rei_zip, rei_city_name, fumigation_type, target_pest, custom_pest, exclusion_subtype)
    #            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    #         (
    #             title,
    #             job_type,
    #             price,
    #             start_date,
    #             end_date,
    #             start_time,
    #             end_time,
    #             time_range,
    #             notes,
    #             technician_id,
    #             two_man,
    #             created_by,
    #             rei_quantity,
    #             rei_zip,
    #             rei_city_name,
    #             fumigation_type,
    #             target_pest,
    #             custom_pest,
    #             exclusion_subtype,
    #         ),
    #     )
    #     conn.commit()
    #     logger.info(
    #         f"Job added by user ID {created_by}: {job_type} from {start_date} to {end_date} at {time_range}"
    #     )
    #     return redirect(url_for("calendar.day_view", selected_date=date))

    # # ✅ This block only runs on GET
    # connection = get_database()
    # cursor = connection.cursor()
    # cursor.execute("SELECT * FROM technicians")
    # technicians = cursor.fetchall()

    # parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
    # return render_template(
    #     "job_form.html",
    #     date=parsed_date,
    #     technicians=technicians,
    #     hide_date_fields=True,
    # )


@job_bp.route("/move_job/<int:job_id>", methods=["POST"])
@login_required
@role_required("manager", "technician", "sales")
def move_job(job_id: int):
    """Move a job to a new start date, preserving its duration.

    Reads the new start from the form field ``new_date``, computes the original span (``end_date - start_date``), applies the same duration from the new start, updates audit fields, and logs.

    Args:
        job_id (int): Identifier of the job to move.

    Returns:
        Response: Redirect to the referrer or ``calendar.index``.  Returns a 404 response if the job is not found.
    """
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
@role_required("manager", "sales")
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
@role_required("manager", "sales")
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
                request.form["price"],
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
