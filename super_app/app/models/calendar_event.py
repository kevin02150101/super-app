"""行事曆事件 + 會議室 Model(移植自 calendar 原專案,單使用者版)。"""
from __future__ import annotations

from datetime import datetime

from ..extensions import db


class MeetingRoom(db.Model):
    __tablename__ = "meeting_rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    capacity = db.Column(db.Integer, default=10)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship(
        "CalendarEvent", back_populates="meeting_room", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "capacity": self.capacity,
            "description": self.description,
            "is_active": self.is_active,
        }


class CalendarEvent(db.Model):
    __tablename__ = "calendar_events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False)
    all_day = db.Column(db.Boolean, default=False)
    event_type = db.Column(db.String(20), default="general")  # general | meeting
    meeting_room_id = db.Column(
        db.Integer, db.ForeignKey("meeting_rooms.id"), nullable=True
    )
    status = db.Column(db.String(20), default="confirmed")
    admin_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    meeting_room = db.relationship("MeetingRoom", back_populates="bookings")

    @property
    def color(self) -> str:
        if self.event_type == "general":
            return "#3788d8"
        return {
            "pending": "#ffc107",
            "approved": "#198754",
            "rejected": "#dc3545",
        }.get(self.status, "#6c757d")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start": self.start_time.isoformat() if self.start_time else None,
            "end": self.end_time.isoformat() if self.end_time else None,
            "allDay": self.all_day,
            "event_type": self.event_type,
            "meeting_room_id": self.meeting_room_id,
            "meeting_room_name": self.meeting_room.name if self.meeting_room else None,
            "status": self.status,
            "admin_note": self.admin_note,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
