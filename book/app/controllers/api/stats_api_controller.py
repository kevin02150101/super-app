from flask import Blueprint, jsonify

from app.services.stats_service import StatsService

stats_api_bp = Blueprint("stats_api", __name__, url_prefix="/api/v1/stats")
_service = StatsService()


@stats_api_bp.get("/dashboard")
def dashboard():
    return jsonify({"success": True, "data": _service.dashboard(), "message": "ok"})
