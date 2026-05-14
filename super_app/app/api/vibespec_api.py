"""Vibe Spec 產生 Web API。"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.vibespec_service import VibeSpecError, VibeSpecService

vibespec_api = Blueprint("vibespec_api", __name__)


@vibespec_api.post("/generate")
def generate():
    data = request.get_json(silent=True) or {}
    idea = data.get("idea", "")
    tech_stack = data.get("tech_stack") or None
    try:
        result = VibeSpecService().generate(idea, tech_stack)
    except VibeSpecError as exc:
        return jsonify({"success": False, "message": str(exc)}), exc.status
    return jsonify({"success": True, "data": result})


@vibespec_api.get("/history")
def history():
    return jsonify({"success": True, "data": VibeSpecService().history()})


@vibespec_api.get("/records/<int:record_id>")
def get_record(record_id: int):
    data = VibeSpecService().get(record_id)
    if not data:
        return jsonify({"success": False, "message": "查無紀錄"}), 404
    return jsonify({"success": True, "data": data})
