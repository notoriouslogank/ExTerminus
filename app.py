from pathlib import Path
from flask import Flask, render_template, session, request
from datetime import date, datetime
from calendar import Calendar
from .config import Config
from .logger import setup_logger
from .routes import register_routes
from .db import init_db, get_database, ensure_pragmas

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR/"templates"
STATIC_DIR = BASE_DIR/"static"

def create_app():
    app = Flask(__name__, static_folder=str(STATIC_DIR), template_folder=str(TEMPLATES_DIR))
    app.config.from_object(Config)

    app.logger = setup_logger()
    app.logger.debug("App starting with config loaded.")

    init_db()
    ensure_pragmas()

    @app.context_processor
    def inject_globals():
        return {"today": date.today(), "now": datetime.now()}

    register_routes(app)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)