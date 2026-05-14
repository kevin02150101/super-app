from flask import Blueprint, render_template
from flask_login import login_required, current_user

from services.stats_service import StatsService

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.get("/")
@login_required
def index():
    kpi = StatsService.kpi_summary(current_user.id)
    return render_template("dashboard/index.html", kpi=kpi)
