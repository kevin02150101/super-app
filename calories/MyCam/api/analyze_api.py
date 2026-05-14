from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from extensions import csrf, limiter
from services.analysis_service import AnalysisService

bp = Blueprint("analyze_api", __name__, url_prefix="/api")


@bp.post("/analyze")
@csrf.exempt
@login_required
@limiter.limit("10/minute")
def analyze():
    file = request.files.get("image")
    analysis = AnalysisService.analyze(current_user.id, file)
    return jsonify(ok=True, data=analysis.to_dict()), 201
