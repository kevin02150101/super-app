from datetime import datetime

from app.extensions import db


class SearchQuery(db.Model):
    __tablename__ = "search_queries"

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False, index=True)
    result_count = db.Column(db.Integer, nullable=False, default=0)
    duration_ms = db.Column(db.Integer, nullable=False, default=0)
    source = db.Column(db.String(50), nullable=False, default="books.com.tw")
    primary_category = db.Column(db.String(50), nullable=True, index=True)
    summary_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )

    results = db.relationship(
        "BookResult",
        back_populates="search_query",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "keyword": self.keyword,
            "result_count": self.result_count,
            "duration_ms": self.duration_ms,
            "source": self.source,
            "primary_category": self.primary_category,
            "summary_text": self.summary_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
