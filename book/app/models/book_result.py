from datetime import datetime

from app.extensions import db


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
    authors = db.Column(db.String(500), nullable=True)
    publisher = db.Column(db.String(200), nullable=True)
    published_at = db.Column(db.String(50), nullable=True)
    price = db.Column(db.Integer, nullable=True)
    image_url = db.Column(db.String(1000), nullable=True)
    product_url = db.Column(db.String(1000), nullable=True)
    category = db.Column(db.String(50), nullable=True, index=True)
    description = db.Column(db.Text, nullable=True)
    summary = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

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
            "category": self.category,
            "description": self.description,
            "summary": self.summary,
        }
