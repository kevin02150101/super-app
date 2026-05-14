"""卡路里分析 Web API。"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.calorie_service import AnalysisService, CalorieError

calories_api = Blueprint("calories_api", __name__)


@calories_api.post("/analyze")
def analyze():
    file = request.files.get("image")
    if not file:
        return jsonify({"success": False, "message": "請上傳影像欄位 image"}), 400
    try:
        data = AnalysisService.analyze(file)
    except CalorieError as exc:
        return (
            jsonify({"success": False, "code": exc.code, "message": str(exc)}),
            exc.status,
        )
    return jsonify({"success": True, "data": data})


@calories_api.get("/analyses")
def list_analyses():
    return jsonify({"success": True, "data": AnalysisService.list_recent()})


@calories_api.get("/analyses/<int:analysis_id>")
def get_analysis(analysis_id: int):
    data = AnalysisService.get(analysis_id)
    if not data:
        return jsonify({"success": False, "message": "查無紀錄"}), 404
    return jsonify({"success": True, "data": data})


@calories_api.delete("/analyses/<int:analysis_id>")
def delete_analysis(analysis_id: int):
    ok = AnalysisService.delete(analysis_id)
    if not ok:
        return jsonify({"success": False, "message": "查無紀錄"}), 404
    return jsonify({"success": True, "message": "已刪除"})
