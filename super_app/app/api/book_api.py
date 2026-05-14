"""書籍查詢 Web API。"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.book_service import BookSearchService

book_api = Blueprint("book_api", __name__)


@book_api.post("/search")
def search():
    data = request.get_json(silent=True) or {}
    keyword = (data.get("keyword") or "").strip()
    if not keyword:
        return jsonify({"success": False, "message": "請提供 keyword"}), 400
    try:
        result = BookSearchService().search(keyword)
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "message": f"爬蟲失敗:{exc}"}), 502
    return jsonify({"success": True, "data": result})


@book_api.get("/history")
def history():
    return jsonify({"success": True, "data": BookSearchService().history()})


@book_api.get("/queries/<int:query_id>")
def query_detail(query_id: int):
    detail = BookSearchService().detail(query_id)
    if not detail:
        return jsonify({"success": False, "message": "查無紀錄"}), 404
    return jsonify({"success": True, "data": detail})


@book_api.get("/stats")
def stats():
    return jsonify({"success": True, "data": BookSearchService().stats()})
