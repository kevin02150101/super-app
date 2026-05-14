"""卡路里 MVC Controller。"""
from flask import Blueprint, render_template

calories_bp = Blueprint("calories", __name__)


@calories_bp.get("/")
def index():
    return render_template("calories/index.html", active="calories")
