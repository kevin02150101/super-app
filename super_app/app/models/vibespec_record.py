"""Vibe Spec 規格產出紀錄 Model。"""
from __future__ import annotations

from datetime import datetime

from ..extensions import db


class VibeSpecRecord(db.Model):
    __tablename__ = "vibespec_records"

    id = db.Column(db.Integer, primary_key=True)
    idea = db.Column(db.String(500), nullable=False)
    tech_stack = db.Column(db.String(500))
    spec_markdown = db.Column(db.Text, nullable=False)
    source_model = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "idea": self.idea,
            "tech_stack": self.tech_stack,
            "spec_markdown": self.spec_markdown,
            "source_model": self.source_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
