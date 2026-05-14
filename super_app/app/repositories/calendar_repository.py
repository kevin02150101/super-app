"""行事曆 Repository(移植自 calendar 原專案,單使用者版)。"""
from __future__ import annotations

from datetime import datetime

from ..extensions import db
from ..models.calendar_event import CalendarEvent, MeetingRoom


class CalendarEventRepository:
    @staticmethod
    def get_by_id(event_id: int) -> CalendarEvent | None:
        return db.session.get(CalendarEvent, event_id)

    @staticmethod
    def list_all(
        start: datetime | None = None, end: datetime | None = None
    ) -> list[CalendarEvent]:
        q = CalendarEvent.query
        if start:
            q = q.filter(CalendarEvent.end_time >= start)
        if end:
            q = q.filter(CalendarEvent.start_time <= end)
        return q.order_by(CalendarEvent.start_time).all()

    @staticmethod
    def pending_bookings() -> list[CalendarEvent]:
        return (
            CalendarEvent.query.filter_by(event_type="meeting", status="pending")
            .order_by(CalendarEvent.created_at.desc())
            .all()
        )

    @staticmethod
    def check_room_conflict(
        room_id: int,
        start: datetime,
        end: datetime,
        exclude_id: int | None = None,
    ) -> bool:
        q = (
            CalendarEvent.query.filter_by(meeting_room_id=room_id)
            .filter(CalendarEvent.status.in_(["pending", "approved"]))
            .filter(CalendarEvent.start_time < end)
            .filter(CalendarEvent.end_time > start)
        )
        if exclude_id:
            q = q.filter(CalendarEvent.id != exclude_id)
        return q.count() > 0

    @staticmethod
    def create(**kwargs) -> CalendarEvent:
        event = CalendarEvent(**kwargs)
        db.session.add(event)
        return event

    @staticmethod
    def update(event: CalendarEvent, **kwargs) -> CalendarEvent:
        for k, v in kwargs.items():
            if hasattr(event, k):
                setattr(event, k, v)
        return event

    @staticmethod
    def delete(event: CalendarEvent) -> None:
        db.session.delete(event)


class MeetingRoomRepository:
    @staticmethod
    def get_by_id(room_id: int) -> MeetingRoom | None:
        return db.session.get(MeetingRoom, room_id)

    @staticmethod
    def get_active() -> list[MeetingRoom]:
        return (
            MeetingRoom.query.filter_by(is_active=True)
            .order_by(MeetingRoom.name)
            .all()
        )

    @staticmethod
    def create(name: str, location: str, capacity: int, description: str = "") -> MeetingRoom:
        room = MeetingRoom(
            name=name, location=location, capacity=capacity, description=description
        )
        db.session.add(room)
        return room
