from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint("capture", __name__, url_prefix="/capture")


@bp.get("/")
@login_required
def index():
    return render_template("capture/index.html")
