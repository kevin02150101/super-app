"""Vibe Spec Repository。"""
from __future__ import annotations

from ..extensions import db
from ..models.vibespec_record import VibeSpecRecord


class VibeSpecRepository:
    @staticmethod
    def create(record: VibeSpecRecord) -> VibeSpecRecord:
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def list_recent(limit: int = 30) -> list[VibeSpecRecord]:
        return (
            VibeSpecRecord.query.order_by(VibeSpecRecord.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get(record_id: int) -> VibeSpecRecord | None:
        return db.session.get(VibeSpecRecord, record_id)
