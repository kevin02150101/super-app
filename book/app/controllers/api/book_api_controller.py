from flask import Blueprint, jsonify, request

from app.services.search_record_service import SearchRecordService

book_api_bp = Blueprint("book_api", __name__, url_prefix="/api/v1/books")
_service = SearchRecordService()


@book_api_bp.post("/search")
def search_books():
    payload = request.get_json(silent=True) or {}
    keyword = (payload.get("keyword") or request.args.get("keyword") or "").strip()
    if not keyword:
        return (
            jsonify({"success": False, "data": None, "message": "keyword Can't be empty"}),
            400,
        )
    try:
        data = _service.search_and_store(keyword)
    except ValueError as e:
        return jsonify({"success": False, "data": None, "message": str(e)}), 400
    except Exception as e:  # Scraping failed
        return (
            jsonify(
                {"success": False, "data": None, "message": f"Search failed: {e}"}
            ),
            502,
        )
    return jsonify({"success": True, "data": data, "message": "ok"}), 200
