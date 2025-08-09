from .calendar_routes import calendar_bp
from .auth_routes import auth_bp
from .job_routes import job_bp
from .admin_routes import admin_bp

def register_routes(app):
    app.register_blueprint(calendar_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(admin_bp)