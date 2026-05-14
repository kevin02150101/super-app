from sqlalchemy import func

from app.extensions import db
from app.models.book_result import BookResult


class BookResultRepository:
    def add_many(self, results: list[BookResult]) -> list[BookResult]:
        db.session.add_all(results)
        db.session.commit()
        return results

    def find_by_query_id(self, query_id: int) -> list[BookResult]:
        return (
            BookResult.query.filter_by(query_id=query_id)
            .order_by(BookResult.id.asc())
            .all()
        )

    def count_total(self) -> int:
        return db.session.query(func.count(BookResult.id)).scalar() or 0

    def avg_price(self) -> float:
        v = db.session.query(func.avg(BookResult.price)).scalar()
        return float(v) if v is not None else 0.0

    def top_publishers(self, limit: int = 10) -> list[tuple[str, int]]:
        rows = (
            db.session.query(BookResult.publisher, func.count(BookResult.id))
            .filter(BookResult.publisher.isnot(None))
            .filter(BookResult.publisher != "")
            .group_by(BookResult.publisher)
            .order_by(func.count(BookResult.id).desc())
            .limit(limit)
            .all()
        )
        return [(r[0], int(r[1])) for r in rows]

    def category_distribution(self) -> list[tuple[str, int]]:
        rows = (
            db.session.query(BookResult.category, func.count(BookResult.id))
            .filter(BookResult.category.isnot(None))
            .group_by(BookResult.category)
            .order_by(func.count(BookResult.id).desc())
            .all()
        )
        return [(r[0], int(r[1])) for r in rows]
