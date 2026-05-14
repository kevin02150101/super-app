"""課本摘要 MVC Controller。"""
from flask import Blueprint, render_template

summary_bp = Blueprint("summary", __name__)


@summary_bp.get("/")
def index():
    return render_template("summary/index.html", active="summary")
