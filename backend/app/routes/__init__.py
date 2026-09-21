from .auth import auth_bp
from .dashboard import dashboard_bp
from .exams import exams_bp
from .records import records_bp
from .security import security_bp
from .warnings import warnings_bp


def register_blueprints(app):
    for bp in (auth_bp, exams_bp, records_bp, warnings_bp, dashboard_bp, security_bp):
        app.register_blueprint(bp)
