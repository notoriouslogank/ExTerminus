from functools import wraps
from flask import session, redirect, url_for, flash, request


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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))

        exempt = {"auth.force_password_reset", "auth.logout", "auth.login", "static"}
        if session.get("must_change_pw") and request.endpoint not in exempt:
            return redirect(url_for("auth.force_password_reset"))

        return f(*args, **kwargs)

    return decorated_function
