from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

bp = Blueprint("home", __name__)


@bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("home/index.html")
