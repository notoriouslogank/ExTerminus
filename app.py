"""Application factory and global Flask wiring for ExTerminus.

Responsibilities:
    - Load environment (.env), config, and logging.
    - Initialize CSRF protection, DB (schema + pragmas), and blueprints.
    - Provide common Jinja filters/context (e.g., ``fmt_ts``, ``today``, version)
    - Register friendly error handlers (404/500, CSRF).
"""

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, flash, g, redirect, render_template, request, url_for
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError, generate_csrf

from .db import ensure_pragmas, init_db
from .routes import register_routes
from .utils.config import Config
from .utils.logger import setup_logger
from .utils.version import APP_VERSION

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

DISPLAY_TZ = ZoneInfo("America/New_York")
ASSUME_UTC = True


def fmt_ts(value):
    """Render a timestamp-like value as a friendly local string.

    Accepts a ``datetime`` or a string that can be parsed into a datetime.  If the input is naive (no tzinfo), a timezone is assumed based on ``ASSUME_UTC`` (UTC if true, otherwise the display zone).  Output is converted to ``DISPLAY_TZ`` and formatted as ``"Month DD, YYYY at HH:MM AM/PM"``.

    Args:
        value: A ``datetime`` or str that looks like ISO (or common SQL formats: ``%Y-%m-%d %H:%M:%S[.%f]``).  Falsy values return ``""``.

    Returns:
        str: The formatted timestamp, or the original string if parsing fails, or ``""`` if ``value`` is falsy.
    """
    if not value:
        return ""
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value)
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.strptime(s, fmt)
                    break
                except ValueError:
                    dt = None
            if dt is None:
                return s
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC") if ASSUME_UTC else DISPLAY_TZ)
    dt = dt.astimezone(DISPLAY_TZ)

    return dt.strftime("%B %d, %Y at %I:%M %p")


def create_app():
    """Create and configure the Flask application.

    Sets up configuration, CSRF protection, logging, DB initialization, Jinja filters/context, error handlers, and registers all blueprints.

    Raises:
        RuntimeError: SECRET_KEY must be set in production.

    Returns:
        Flask: A fully-configured Flask application instance.
    """
    app = Flask(
        __name__, static_folder=str(STATIC_DIR), template_folder=str(TEMPLATES_DIR)
    )
    app.config.from_object(Config)

    app.jinja_env.filters["fmt_ts"] = fmt_ts

    if not app.debug and app.config.get("SECRET_KEY") in (
        None,
        "",
        "dev-insecure-change-me",
    ):
        raise RuntimeError("SECRET_KEY must be set in production.")

    CSRFProtect(app)

    logger = setup_logger()  # type: ignore
    logger.debug("App starting with config loaded.")

    @app.context_processor
    def inject_csrf():
        """Expose ``csrf_token`` helper to templates."""
        return dict(csrf_token=generate_csrf)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError):
        """Redirect with a user-friendly message when CSRF fails."""
        flash("Your session expired or the form was invalid. Please try again", "error")
        return redirect(request.referrer or url_for("auth.login")), 303

    @app.errorhandler(404)
    def not_found(e):
        """Render teh generic 404 error page."""
        return render_template("errors.html", code=404), 404

    @app.errorhandler(500)
    def server_error(e):
        """Render the generic 500 error page."""
        return render_template("errors.html", code=500), 500

    init_db()
    ensure_pragmas()

    @app.teardown_appcontext
    def close_db(_exc):
        """Commit/rollback and close any DB connection stored on ``g``."""
        db = g.pop("db", None)
        if db is not None:
            try:
                db.commit()
            except Exception:
                db.rollback()
            db.close()

    @app.context_processor
    def inject_globals():
        """Provide ``today`` and ``now`` to all templates."""
        return {"today": date.today(), "now": datetime.now()}

    @app.context_processor
    def inject_app_version():
        """Provide ``app_version`` (semantic app version) to templates."""
        return dict(app_version=APP_VERSION)

    register_routes(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
