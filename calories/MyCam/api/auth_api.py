from flask import Blueprint, request, jsonify

from extensions import csrf
from services.auth_service import AuthService

bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")


@bp.post("/register")
@csrf.exempt
def register():
    data = request.get_json(silent=True) or request.form
    user = AuthService.register(
        email=data.get("email"),
        password=data.get("password"),
        nickname=data.get("nickname", ""),
    )
    return jsonify(ok=True, data=user.to_dict()), 201


@bp.post("/login")
@csrf.exempt
def login():
    data = request.get_json(silent=True) or request.form
    user = AuthService.login(
        email=data.get("email"),
        password=data.get("password"),
        remember=bool(data.get("remember", True)),
    )
    return jsonify(ok=True, data=user.to_dict())


@bp.post("/logout")
@csrf.exempt
def logout():
    AuthService.logout()
    return jsonify(ok=True)
