from flask import Blueprint, jsonify, render_template

home_bp = Blueprint("home", __name__, url_prefix="/")


@home_bp.get("/")
def index():
    return render_template("home/index.html", title="Book search", active="home")


@home_bp.get("/healthz")
def healthz():
    return jsonify({"ok": True}), 200
