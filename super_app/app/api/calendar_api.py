"""行事曆 Web API。"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.calendar_service import CalendarEventService, MeetingRoomService

calendar_api = Blueprint("calendar_api", __name__)


@calendar_api.get("/events")
def list_events():
    start = request.args.get("start")
    end = request.args.get("end")
    return jsonify({"success": True, "data": CalendarEventService.get_events(start, end)})


@calendar_api.post("/events")
def create_event():
    data = request.get_json(silent=True) or {}
    res = CalendarEventService.create_event(
        title=data.get("title", ""),
        start_time=data.get("start_time", ""),
        end_time=data.get("end_time", ""),
        event_type=data.get("event_type", "general"),
        description=data.get("description", ""),
        all_day=bool(data.get("all_day", False)),
        meeting_room_id=data.get("meeting_room_id"),
    )
    return jsonify(res), (200 if res["success"] else 400)


@calendar_api.delete("/events/<int:event_id>")
def delete_event(event_id: int):
    res = CalendarEventService.delete_event(event_id)
    return jsonify(res), (200 if res["success"] else 404)


@calendar_api.get("/bookings/pending")
def pending_bookings():
    return jsonify({"success": True, "data": CalendarEventService.pending_bookings()})


@calendar_api.put("/bookings/<int:event_id>/approve")
def approve_booking(event_id: int):
    data = request.get_json(silent=True) or {}
    res = CalendarEventService.approve(event_id, data.get("admin_note", ""))
    return jsonify(res), (200 if res["success"] else 400)


@calendar_api.put("/bookings/<int:event_id>/reject")
def reject_booking(event_id: int):
    data = request.get_json(silent=True) or {}
    res = CalendarEventService.reject(event_id, data.get("admin_note", ""))
    return jsonify(res), (200 if res["success"] else 400)


@calendar_api.get("/rooms")
def list_rooms():
    return jsonify({"success": True, "data": MeetingRoomService.list_rooms()})


@calendar_api.post("/rooms")
def create_room():
    data = request.get_json(silent=True) or {}
    res = MeetingRoomService.create_room(
        name=data.get("name", ""),
        location=data.get("location", ""),
        capacity=int(data.get("capacity") or 10),
        description=data.get("description", ""),
    )
    return jsonify(res), (200 if res["success"] else 400)
