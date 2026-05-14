"""行事曆 + 會議室 Service(移植自 calendar 原專案,單使用者版)。"""
from __future__ import annotations

from datetime import datetime

from ..extensions import db
from ..repositories.calendar_repository import (
    CalendarEventRepository,
    MeetingRoomRepository,
)


class CalendarEventService:
    @staticmethod
    def get_events(start: str | None = None, end: str | None = None) -> list[dict]:
        s = datetime.fromisoformat(start) if start else None
        e = datetime.fromisoformat(end) if end else None
        return [ev.to_dict() for ev in CalendarEventRepository.list_all(s, e)]

    @staticmethod
    def create_event(
        title: str,
        start_time: str,
        end_time: str,
        event_type: str = "general",
        description: str = "",
        all_day: bool = False,
        meeting_room_id: int | None = None,
    ) -> dict:
        if not title or not title.strip():
            return {"success": False, "message": "事件標題不可為空"}
        try:
            sdt = datetime.fromisoformat(start_time)
            edt = datetime.fromisoformat(end_time)
        except (TypeError, ValueError):
            return {"success": False, "message": "時間格式錯誤"}
        if edt <= sdt:
            return {"success": False, "message": "結束時間必須晚於開始時間"}

        status = "confirmed"
        if event_type == "meeting":
            if not meeting_room_id:
                return {"success": False, "message": "預約會議廳時必須選擇會議廳"}
            if CalendarEventRepository.check_room_conflict(meeting_room_id, sdt, edt):
                return {"success": False, "message": "該會議廳在此時段已被預約"}
            status = "pending"

        event = CalendarEventRepository.create(
            title=title.strip(),
            description=description,
            start_time=sdt,
            end_time=edt,
            all_day=all_day,
            event_type=event_type,
            meeting_room_id=meeting_room_id,
            status=status,
        )
        db.session.commit()
        return {"success": True, "message": "事件已建立", "data": event.to_dict()}

    @staticmethod
    def delete_event(event_id: int) -> dict:
        event = CalendarEventRepository.get_by_id(event_id)
        if not event:
            return {"success": False, "message": "事件不存在"}
        CalendarEventRepository.delete(event)
        db.session.commit()
        return {"success": True, "message": "事件已刪除"}

    @staticmethod
    def pending_bookings() -> list[dict]:
        return [e.to_dict() for e in CalendarEventRepository.pending_bookings()]

    @staticmethod
    def approve(event_id: int, admin_note: str = "") -> dict:
        event = CalendarEventRepository.get_by_id(event_id)
        if not event or event.event_type != "meeting" or event.status != "pending":
            return {"success": False, "message": "預約不存在或無法核准"}
        CalendarEventRepository.update(event, status="approved", admin_note=admin_note)
        db.session.commit()
        return {"success": True, "message": "預約已核准", "data": event.to_dict()}

    @staticmethod
    def reject(event_id: int, admin_note: str = "") -> dict:
        event = CalendarEventRepository.get_by_id(event_id)
        if not event or event.event_type != "meeting" or event.status != "pending":
            return {"success": False, "message": "預約不存在或無法駁回"}
        CalendarEventRepository.update(event, status="rejected", admin_note=admin_note)
        db.session.commit()
        return {"success": True, "message": "預約已駁回", "data": event.to_dict()}


class MeetingRoomService:
    @staticmethod
    def list_rooms() -> list[dict]:
        return [r.to_dict() for r in MeetingRoomRepository.get_active()]

    @staticmethod
    def create_room(name: str, location: str, capacity: int, description: str = "") -> dict:
        if not name or not name.strip():
            return {"success": False, "message": "會議廳名稱不可為空"}
        room = MeetingRoomRepository.create(
            name=name.strip(), location=location, capacity=capacity, description=description
        )
        db.session.commit()
        return {"success": True, "message": "會議廳已建立", "data": room.to_dict()}
