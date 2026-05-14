"""課本摘要 Repository。"""
from __future__ import annotations

from ..extensions import db
from ..models.summary_record import SummaryRecord


class SummaryRepository:
    @staticmethod
    def create(record: SummaryRecord) -> SummaryRecord:
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def list_recent(limit: int = 30) -> list[SummaryRecord]:
        return (
            SummaryRecord.query.order_by(SummaryRecord.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get(record_id: int) -> SummaryRecord | None:
        return db.session.get(SummaryRecord, record_id)
