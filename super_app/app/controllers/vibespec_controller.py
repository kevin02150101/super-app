"""Vibe Spec MVC Controller。"""
from flask import Blueprint, render_template

vibespec_bp = Blueprint("vibespec", __name__)


@vibespec_bp.get("/")
def index():
    return render_template("vibespec/index.html", active="vibespec")
