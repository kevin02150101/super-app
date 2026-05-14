from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, logout_user

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/login")
def login_page():
    return render_template("auth/login.html")


@bp.get("/register")
def register_page():
    return render_template("auth/register.html")


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home.index"))
