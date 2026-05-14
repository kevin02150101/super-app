"""書籍查詢 Model - 對應博客來爬蟲結果。"""
from __future__ import annotations

from datetime import datetime

from ..extensions import db


class SearchQuery(db.Model):
    __tablename__ = "search_queries"

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False, index=True)
    result_count = db.Column(db.Integer, nullable=False, default=0)
    duration_ms = db.Column(db.Integer, nullable=False, default=0)
    source = db.Column(db.String(50), nullable=False, default="books.com.tw")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BookResult(db.Model):
    __tablename__ = "book_results"

    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(
        db.Integer,
        db.ForeignKey("search_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(500), nullable=False)
    authors = db.Column(db.String(500))
    publisher = db.Column(db.String(200))
    published_at = db.Column(db.String(50))
    price = db.Column(db.Integer)
    image_url = db.Column(db.String(1000))
    product_url = db.Column(db.String(1000))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    search_query = db.relationship("SearchQuery", back_populates="results")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "query_id": self.query_id,
            "title": self.title,
            "authors": self.authors,
            "publisher": self.publisher,
            "published_at": self.published_at,
            "price": self.price,
            "image_url": self.image_url,
            "product_url": self.product_url,
            "description": self.description,
        }
