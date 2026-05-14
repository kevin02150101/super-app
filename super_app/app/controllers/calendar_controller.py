"""行事曆 MVC Controller。"""
from flask import Blueprint, render_template

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.get("/")
def index():
    return render_template("calendar/index.html", active="calendar")
