from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from services.stats_service import StatsService

bp = Blueprint("stats_api", __name__, url_prefix="/api/stats")


@bp.get("/summary")
@login_required
def summary():
    return jsonify(ok=True, data=StatsService.kpi_summary(current_user.id))


@bp.get("/calories")
@login_required
def calories():
    days = min(int(request.args.get("days", 30)), 365)
    return jsonify(ok=True, data=StatsService.calories_timeseries(current_user.id, days=days))


@bp.get("/categories")
@login_required
def categories():
    return jsonify(ok=True, data=StatsService.category_distribution(current_user.id))
