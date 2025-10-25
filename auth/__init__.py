from flask import Blueprint

# Define the blueprint early so other modules can import auth.auth_bp without triggering a circular import.
auth_bp = Blueprint("auth", __name__, template_folder="templates")

# Import routes after auth_bp is defined so routes can register handlers on it.
from . import routes  # noqa: E402,F401
