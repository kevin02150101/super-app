"""課本摘要 Web API。"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.summary_service import SummaryError, SummaryService

summary_api = Blueprint("summary_api", __name__)


@summary_api.post("/generate")
def generate():
    data = request.get_json(silent=True) or {}
    keyword = data.get("keyword", "")
    try:
        result = SummaryService().generate(keyword)
    except SummaryError as exc:
        return jsonify({"success": False, "message": str(exc)}), exc.status
    return jsonify({"success": True, "data": result})


@summary_api.get("/history")
def history():
    return jsonify({"success": True, "data": SummaryService().history()})


@summary_api.get("/records/<int:record_id>")
def get_record(record_id: int):
    data = SummaryService().get(record_id)
    if not data:
        return jsonify({"success": False, "message": "Record not found"}), 404
    return jsonify({"success": True, "data": data})
