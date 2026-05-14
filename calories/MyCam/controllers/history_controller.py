from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from services.analysis_service import AnalysisService

bp = Blueprint("history", __name__, url_prefix="/history")


@bp.get("/")
@login_required
def list_page():
    return render_template("history/list.html")


@bp.get("/<int:analysis_id>")
@login_required
def detail_page(analysis_id):
    analysis = AnalysisService.get(current_user.id, analysis_id)
    if not analysis:
        abort(404)
    return render_template("history/detail.html", analysis=analysis)
