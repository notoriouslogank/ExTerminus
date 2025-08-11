from dotenv import load_dotenv
from pathlib import Path
from flask import Flask, g, request, redirect, url_for, flash, render_template
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError, generate_csrf
from datetime import date, datetime
from .utils.config import Config
from .utils.logger import setup_logger
from .routes import register_routes
from .db import init_db, ensure_pragmas
from .utils.version import APP_VERSION
from zoneinfo import ZoneInfo

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

DISPLAY_TZ = ZoneInfo("America/New_York")
ASSUME_UTC = True


def fmt_ts(value):
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
        return dict(csrf_token=generate_csrf)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("Your session expired or the form was invalid. Please try again", "error")
        return redirect(request.referrer or url_for("auth.login")), 303

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors.html", code=404), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors.html", code=500), 500

    init_db()
    ensure_pragmas()

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            try:
                db.commit()
            except Exception:
                db.rollback()
            db.close()

    @app.context_processor
    def inject_globals():
        return {"today": date.today(), "now": datetime.now()}

    @app.context_processor
    def inject_app_version():
        return dict(app_version=APP_VERSION)

    register_routes(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
