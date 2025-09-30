"""Admin routes: user management (list/create/update role/reset password/delete).

Notes:
    - Access is restricted to role ``"admin"`` via ``@role_required("admin")``.
    - Creating a user sets ``must_reset_password = 1`` so the first login forces a password change.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from db import get_database
from utils.decorators import role_required
from utils.logger import setup_logger

admin_bp = Blueprint("admin", __name__)
logger = setup_logger()


@admin_bp.route("/admin/users", methods=["GET", "POST"])
@role_required("admin")
def admin_users():
    """List and manage users (admin only).

    Handles GET (render table + form) and POST (mutations). Supports:
        - ``action == "update_role"``: Change a user's role; normalizes ``"tech"`` -> ``"technician"``.  If the rule becomes ``"technician"``, ensures a row in ``technicians`` (uses first/last or username).
        - ``action == "reset_password"``: Set password to default ``"changeme"`` (auth layer forces reset).
        - ``acton == "delete_user"``: Permanently remove the user.
        - otherwise: Create a new user with ``must_reset_password = 1``; if role is technician, add to ``technicians``.

    Form fields (vary by action):
        - Common: ``action`` (str)
        - Update/Delete/Reset: ``update_user_id`` (int as str)
        - Update role: ``role`` (str: ``admin`` | ``manager`` | ``technician`` | ``sales`` | ``tech``)
        Create: ``first_name`` (str), ``last_name`` (str), ``username`` (str), ``password`` (str, optional; default to ``"changeme"``), ``role`` (str)

    Returns:
        Response: On GET, render ``admin_users.html`` with the users list.  On POST, perform the action, flash a status, and redirect back to ``admin.admin_users`` (PRG pattern).
    """

    conn = get_database()
    cursor = conn.cursor()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_role":
            user_id = request.form.get("update_user_id")
            new_role = (request.form.get("role") or "").strip().lower()
            if new_role == "tech":
                new_role = "technician"

            # fetch user so we can build tech name
            row = cursor.execute(
                "SELECT first_name, last_name, username FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                flash("User not found.", "error")
                return redirect(url_for("admin.admin_users"))

            cursor.execute(
                "UPDATE users SET role = ? WHERE id = ?", (new_role, user_id)
            )

            if new_role == "technician":
                full_name = f"{(row['first_name'] or '').strip()} {(row['last_name'] or '').strip()}".strip()
                tech_name = full_name or row["username"]
                cursor.execute(
                    "INSERT OR IGNORE INTO technicians (name) VALUES (?)", (tech_name,)
                )

            conn.commit()
            flash("Role updated.")
            logger.info(f"Admin updated role for user ID {user_id} to {new_role}.")
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
                """INSERT INTO users (first_name, last_name, username, password, role, must_reset_password) VALUES (?, ?, ?, ?, ?, 1)""",
                (first, last, username, hashed, role),
            )

            if role.lower() in ("technician", "tech"):
                full_name = (
                    f"{(first or '').strip()} {(last or '').strip()}".strip()
                    or username
                )
                cursor.execute(
                    "INSERT OR IGNORE INTO technicians (name) VALUES (?)", (full_name,)
                )
            conn.commit()
            flash(f"User {username} created with role {role}.")
            return redirect(url_for("admin.admin_users"))

    cursor.execute("SELECT * FROM users ORDER BY last_name, first_name")
    users = cursor.fetchall()
    conn.close()

    return render_template("admin_users.html", users=users)
