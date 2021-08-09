"""Allows users to create and edit workout plans"""

from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    session,
    render_template,
)

from helpers import apology, login_required
from db import get_db

bp = Blueprint("planner", __name__, url_prefix="/planner")


@bp.route("/overview", methods=["GET", "POST"])
@login_required
def plans():
    return render_template("plans.html")
