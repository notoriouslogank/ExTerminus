from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from ..db import get_database
from ..utils.logger import setup_logger
from ..utils.decorators import role_required

admin_bp = Blueprint("admin", __name__)
logger = setup_logger()


@admin_bp.route("/admin/users", methods=["GET", "POST"])
@role_required("admin")
def admin_users():
    if not session.get("user") or session["user"].get("role") != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("calendar.index"))

    conn = get_database()
    cursor = conn.cursor()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_role":
            user_id = request.form.get("update_user_id")
            new_role = request.form.get("role")
            cursor.execute(
                "UPDATE users SET role = ? WHERE id = ?", (new_role, user_id)
            )
            conn.commit()
            flash("Role updated.")
            logger.info(f"Admin updated role for user ID {user_id} to {new_role}")
            return redirect(url_for("admin.admin_users"))

        elif action == "reset_password":
            user_id = request.form.get("update_user_id")
            new_pw_hash = generate_password_hash("changeme")
            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?", (new_pw_hash, user_id)
            )
            conn.commit()
            flash("Password reset to 'changeme'.")
            logger.info(f"Admin reset password for user ID {user_id}")
            return redirect(url_for("admin.admin_users"))

        elif action == "delete_user":
            user_id = request.form.get("update_user_id")
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            flash("User deleted.")
            logger.info(f"Admin deleted user ID {user_id}")
            return redirect(url_for("admin.admin_users"))

        else:
            first = request.form["first_name"]
            last = request.form["last_name"]
            username = request.form["username"]
            password = request.form["password"] or "changeme"
            role = request.form["role"]

            hashed = generate_password_hash(password)
            cursor.execute(
                """INSERT INTO users (first_name, last_name, username, password, role) VALUES (?, ?, ?, ?, ?)""",
                (first, last, username, hashed, role),
            )

            conn.commit()
            flash(f"User {username} created with role {role}.")
            return redirect(url_for("admin.admin_users"))

    cursor.execute("SELECT * FROM users ORDER BY last_name, first_name")
    users = cursor.fetchall()
    conn.close()

    return render_template("admin_users.html", users=users)
