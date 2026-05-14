"""首頁 Controller。"""
from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__)


@home_bp.get("/")
def index():
    return render_template("home/index.html")
