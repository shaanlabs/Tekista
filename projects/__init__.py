from flask import Blueprint

projects_bp = Blueprint("projects", __name__, template_folder="templates")

from . import routes as routes  # noqa: E402  # pylint: disable=wrong-import-position
