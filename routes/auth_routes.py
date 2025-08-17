from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
from ..utils.decorators import login_required
from ..db import get_database
from ..utils.logger import setup_logger

auth_bp = Blueprint("auth", __name__)
logger = setup_logger()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
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
    username = session.get("user", {}.get("username", "unknown"))
    session.clear()
    logger.info(f"User '{username}' logged out")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
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
        flash("Password updated succesfully.")
        return redirect(url_for("calendar.index"))
    return render_template("change_password.html")


@auth_bp.route("/force-password-reset", methods=["GET", "POST"])
@login_required
def force_password_reset():
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
