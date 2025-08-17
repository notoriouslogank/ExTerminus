"""Authentication routes: login, logout, password change, and forced reset.

Notes:
    - Sets ``session["user"]`` on login with basic profile fields.
    - Enforces first-login reset via ``session["must_change_pw"]``.
    - Uses CSRF tokens on GET pages that render forms.
"""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import generate_csrf
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_database
from ..utils.decorators import login_required
from ..utils.logger import setup_logger

auth_bp = Blueprint("auth", __name__)
logger = setup_logger()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a user and establish a session.

    On GET, renders the login form (emits a CSRF token).  On POST, verifies credentials against the ``users`` table, sets ``session["user"]`` and ``session["must_change_pw"]`` (true if ``must_reset_password`` is set or if the stored hash matches the default ``"changeme"``), and redirects.

    Form fields:
        - ``username`` (str)
        - ``password`` (str)

    Returns:
        Response: On success, redirect to ``calendar.index``; if a password change is required, redirect to ``auth.force_password_reset`` with a warning flash; on failure, re-render the login form with a flash.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        connection = get_database()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user["password"], password):
            must_change = bool(user["must_reset_password"]) or check_password_hash(
                user["password"], "changeme"
            )

            session["user"] = {
                "user_id": user["id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "username": user["username"],
                "role": user["role"],
            }
            session["must_change_pw"] = must_change

            if must_change:
                flash("Please set a new password to continue.", "warning")
                return redirect(url_for("auth.force_password_reset"))
            logger.info(f"User '{username}' logged in")
            return redirect(url_for("calendar.index"))
        flash("Invalid username or password")
        logger.warning(f"Failed login attempt for username: {username}")
    generate_csrf()
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Clar the current session and return to the login screen.

    Logs a best-effort username for audit, clears the session, and redirects to the login page.

    Returns:
        Response: Redirect to ``auth.login``.
    """
    user = session.get("user") or {}
    username = user.get("username", "unknown")
    session.clear()
    logger.info(f"User '{username}' logged out")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow a logged-in user to change their password.

    On POST, verifies the current password, checks the new/confirm match, updates the stored hash, and redirects to the calendar with a success flash.  On GET, renders the change-password form.

    Form fields:
        - ``current_password`` (str)
        - ``new_password`` (str)
        - ``confirm_password`` (str)

    Returns:
        Response: On success, redirect to ``calendar.index``; on validation errors, redirect back to ``auth.change_password``; on GET, render form.
    """
    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("auth.change_password"))

        user_id = session["user"]["user_id"]
        conn = get_database()
        cursor = conn.cursor()

        cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user or not check_password_hash(user["password"], current_password):
            flash("Password or username is incorrect.")
            return redirect(url_for("auth.change_password"))

        hashed = generate_password_hash(new_password)
        logger.info(f"User ID {user_id} changed their password")
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, user_id))
        conn.commit()
        flash("Password updated successfully.")
        return redirect(url_for("calendar.index"))
    return render_template("change_password.html")


@auth_bp.route("/force-password-reset", methods=["GET", "POST"])
@login_required
def force_password_reset():
    """Enforce a password change before allowing normal navigation.

    Gate triggered when ``session["must_change_pw"]`` is true (e.g., first login with default password).  On POST, validates the new password (length, match, and not equal to ``"changeme"``), updates the hash, clears the ``must_reset_password`` flag, timestamps the change, and disables the gate for this session.

    Form fields:
        - ``new_password`` (str)
        - ``confirm_password`` (str)

    Returns:
        Response: On success, redirect to ``calendar.index`` with a success flash; on validation errors, re-render the reset form with errors; on GET, render the reset form (emits a CSRF token).
    """
    if request.method == "POST":
        new = (request.form.get("new_password") or "").strip()
        confirm = (request.form.get("confirm_password") or "").strip()

        if len(new) < 8:
            flash("Password must be at least 8 characters in length.", "error")
            return render_template("force_password_reset.html")
        if new != confirm:
            flash("Passwords do not match.", "error")
            return render_template("force_password_reset.html")
        if new.lower() == "changeme":
            flash("Nice try. Pick something else.", "error")
            return render_template("force_password_reset.html")

        uid = session["user"]["user_id"]
        conn = get_database()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE users
                SET password = ?,
                    must_reset_password = 0,
                    last_password_change = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (generate_password_hash(new), uid),
        )
        conn.commit()

        session["must_change_pw"] = False
        flash("Password updated.  Welcome aboard.", "success")
        return redirect(url_for("calendar.index"))
    generate_csrf()
    return render_template("force_password_reset.html")
