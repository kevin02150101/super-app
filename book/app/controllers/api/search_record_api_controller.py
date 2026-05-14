from flask import Blueprint, jsonify, request

from app.services.search_record_service import SearchRecordService

search_record_api_bp = Blueprint(
    "search_record_api", __name__, url_prefix="/api/v1/search-records"
)
_service = SearchRecordService()


@search_record_api_bp.get("")
def list_records():
    keyword = (request.args.get("keyword") or "").strip()
    category = (request.args.get("category") or "").strip() or None
    limit = min(int(request.args.get("limit", 50)), 200)
    if keyword:
        data = _service.search_history(keyword, limit=limit, category=category)
    else:
        data = _service.list_recent(limit=limit, category=category)
    return jsonify({"success": True, "data": data, "message": "ok"})


@search_record_api_bp.get("/categories")
def list_categories():
    return jsonify(
        {"success": True, "data": _service.list_categories(), "message": "ok"}
    )


@search_record_api_bp.get("/<int:record_id>")
def get_record(record_id: int):
    data = _service.get_detail(record_id)
    if data is None:
        return (
            jsonify({"success": False, "data": None, "message": "Record not found"}),
            404,
        )
    return jsonify({"success": True, "data": data, "message": "ok"})


@search_record_api_bp.delete("/<int:record_id>")
def delete_record(record_id: int):
    ok = _service.delete(record_id)
    if not ok:
        return (
            jsonify({"success": False, "data": None, "message": "Record not found"}),
            404,
        )
    return jsonify({"success": True, "data": None, "message": "deleted"})
