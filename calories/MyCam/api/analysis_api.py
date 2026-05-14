from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from extensions import csrf
from services.analysis_service import AnalysisService
from errors import MyCamError

bp = Blueprint("analysis_api", __name__, url_prefix="/api/analyses")


@bp.get("")
@login_required
def list_():
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 20)), 100)
    p = AnalysisService.list(current_user.id, page=page, per_page=per_page)
    items = [a.to_dict(include_items=False) for a in p.items]
    return jsonify(ok=True, data={
        "items": items, "page": p.page, "per_page": p.per_page, "total": p.total
    })


@bp.get("/<int:analysis_id>")
@login_required
def detail(analysis_id):
    a = AnalysisService.get(current_user.id, analysis_id)
    if not a:
        raise MyCamError("NOT_FOUND", "Record not found", 404)
    return jsonify(ok=True, data=a.to_dict())


@bp.delete("/<int:analysis_id>")
@csrf.exempt
@login_required
def delete(analysis_id):
    ok = AnalysisService.delete(current_user.id, analysis_id)
    if not ok:
        raise MyCamError("NOT_FOUND", "Record not found", 404)
    return jsonify(ok=True)
