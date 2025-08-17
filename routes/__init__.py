"""Blueprint wiring for ExTerminus routes.

Imports all route blueprints and registers them on a Flask app instance.
"""

from .admin_routes import admin_bp
from .auth_routes import auth_bp
from .calendar_routes import calendar_bp
from .job_routes import job_bp


def register_routes(app) -> None:
    """Register all route blueprints on the given Flask app.

    Args:
        app (Flask): The application instance to configure.

    Returns:
        None
    """
    app.register_blueprint(calendar_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(admin_bp)
