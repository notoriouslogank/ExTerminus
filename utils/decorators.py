"""Auth-related decorators for route protection.

Provides:
    - role_required(*roles): ensure the current session user has one of the allowed roles; otherwise flash and redirect.
    - login_required(func): ensure a user is logged in; additionally enforces a forced-password-reset gate via ``session["must_change_pw"]``.
"""

from functools import wraps

from flask import flash, redirect, request, session, url_for


def role_required(*roles):
    """Decorator factory to restrict a view to specific roles.

    If no user is logged in, redirects to the login page.
    If a user is logged in but their ``role`` is not in ``roles``, a flash message is shown and the user is redirected to the calendar.

    Args:
        *roles: One or more role names (e.g., ``"admin"``, ``"manager"``, ``"technician"``, ``"sales"``).  If empty, any logged-in user passes.

    Returns:
        Callable: A decorator that wraps a Flask view function, preserving metadata via ``functools.wraps``.
    """

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
    """Decorator to require authentication and enforce password-reset gate.

    Behavior:
        - If no ``session["user"]`` is present, redirect to ``auth.login``.
        - If ``session["must_change_pw"]`` is true and the current endpoint is not exempt, redirect to ``auth.force_password_reset``.
        - Otherwise, call the wrapped view.

    Exempt endpoints:
        ``{"auth.force_password_reset", "auth.logout", "auth.login", "static"}``

    Args:
        f: Flask view function to wrap.

    Returns:
        Callable: The wrapped view function with access control applied and metadata preserved via ``functools.wraps``.

    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))

        exempt = {"auth.force_password_reset", "auth.logout", "auth.login", "static"}
        if session.get("must_change_pw") and request.endpoint not in exempt:
            return redirect(url_for("auth.force_password_reset"))

        return f(*args, **kwargs)

    return decorated_function
