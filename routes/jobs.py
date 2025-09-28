from flask import Blueprint, current_app, flash, g, redirect, request, url_for

from utils.decorators import login_required

bp = Blueprint("jobs", __name__, url_prefix="/jobs")


@bp.post("/create")
@login_required
def create():
    svc = current_app.extensions["services"]["jobs"]
    payload = dict(request.form)
    try:
        svc.create_single(payload, g.user)
        flash("Job created.", "success")
        return redirect(url_for("claendar.day_view", date=payload["date"]))
    except Exception as e:
        flash(str(e), "error")
        return redirect(request.referrer or url_for("calendar.index"))


@bp.route("/create-multiday", methods=["POST"])
@login_required
def create_multiday():
    svc = current_app.extensions["services"]["jobs"]
    try:
        payload = svc.normalize_multiday_form(request.form)
        job_id = svc.create_multiday(payload, g.user)
        flash(
            f'Created job #{job_id} "{payload["title"]}" '
            f'({payload["start_date"]} -> {payload["end_date"]}).',
            "success",
        )

        return redirect(url_for("calendar.day_view", date=payload["start_date"]))
    except (ValueError, PermissionError) as e:
        flash(str(e), "error")
        return redirect(request.referrer or url_for("calendar.index"))


@bp.post("/<int:job_id>/move")
@login_required
def move(job_id: int):
    svc = current_app.services["jobs"]
    new_date = request.form.get("new_date")
    try:
        svc.move(job_id, new_date, g.user)
        flash(f"Moved job to {new_date}.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("calendar.day_view", date=new_date))
