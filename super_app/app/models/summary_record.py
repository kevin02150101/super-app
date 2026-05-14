"""SummaryRecord model — stores AI textbook summary + chart payload."""
from __future__ import annotations

import json
from datetime import datetime

from ..extensions import db


class SummaryRecord(db.Model):
    __tablename__ = "summary_records"

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False, index=True)
    summary_text = db.Column(db.Text, nullable=False)
    chart_data = db.Column(db.Text)  # JSON string: {title, type, labels, values}
    source_model = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        graph = None
        if self.chart_data:
            try:
                graph = json.loads(self.chart_data)
            except (TypeError, ValueError):
                graph = None
        return {
            "id": self.id,
            "keyword": self.keyword,
            "summary_text": self.summary_text,
            "graph": graph,
            "source_model": self.source_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
