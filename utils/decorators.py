from functools import wraps
from flask import session, redirect, url_for, flash


def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def inner(*args, **kwargs):
            user = session.get("user")
            if not user:
                return redirect(url_for("auth.login"))
            if roles and user.get("role") not in roles:
                flash("You are not allowed to do that.", "error")
                return redirect(url_for("calendar.index"))
            return f(*args, **kwargs)

        return inner

    return wrapper
