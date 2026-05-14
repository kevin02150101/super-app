from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__, url_prefix="/")


@home_bp.get("/")
def index():
    return render_template("home/index.html", title="Book search", active="home")
