from pathlib import Path
from flask import Flask, g, request, redirect, url_for, flash
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError, generate_csrf
from datetime import date, datetime
from .utils.config import Config
from .utils.logger import setup_logger
from .routes import register_routes
from .db import init_db, ensure_pragmas
from .utils.version import APP_VERSION

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


def create_app():
    app = Flask(
        __name__, static_folder=str(STATIC_DIR), template_folder=str(TEMPLATES_DIR)
    )
    app.config.from_object(Config)

    CSRFProtect(app)

    @app.context_processor
    def inject_csrf():
        return dict(csrf_token=generate_csrf)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("Your session expired or the form was invalid. Please try again", "error")
        return redirect(request.referrer or url_for("auth.login")), 303

    logger = setup_logger()  # type: ignore
    logger.debug("App starting with config loaded.")

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
