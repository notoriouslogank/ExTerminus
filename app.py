from pathlib import Path
from flask import Flask, render_template, session, request, g
from datetime import date, datetime
from calendar import Calendar
from .config import Config
from .logger import setup_logger
from .routes import register_routes
from .db import init_db, get_database, ensure_pragmas
from .utils.version import APP_VERSION

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


def create_app():
    app = Flask(
        __name__, static_folder=str(STATIC_DIR), template_folder=str(TEMPLATES_DIR)
    )
    app.config.from_object(Config)

    app.logger = setup_logger()  # type: ignore
    app.logger.debug("App starting with config loaded.")

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
