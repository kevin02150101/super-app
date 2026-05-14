"""書籍 Repository。"""
from __future__ import annotations

from sqlalchemy import func

from ..extensions import db
from ..models.book_record import BookResult, SearchQuery


class SearchQueryRepository:
    @staticmethod
    def add(query: SearchQuery) -> SearchQuery:
        db.session.add(query)
        db.session.commit()
        return query

    @staticmethod
    def find_recent(limit: int = 50) -> list[SearchQuery]:
        return (
            SearchQuery.query.order_by(SearchQuery.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def find_by_id(query_id: int) -> SearchQuery | None:
        return db.session.get(SearchQuery, query_id)

    @staticmethod
    def top_keywords(limit: int = 10) -> list[tuple[str, int]]:
        rows = (
            db.session.query(SearchQuery.keyword, func.count(SearchQuery.id))
            .group_by(SearchQuery.keyword)
            .order_by(func.count(SearchQuery.id).desc())
            .limit(limit)
            .all()
        )
        return [(k, int(c)) for k, c in rows]


class BookResultRepository:
    @staticmethod
    def add_many(results: list[BookResult]) -> list[BookResult]:
        db.session.add_all(results)
        db.session.commit()
        return results

    @staticmethod
    def find_by_query_id(query_id: int) -> list[BookResult]:
        return (
            BookResult.query.filter_by(query_id=query_id)
            .order_by(BookResult.id.asc())
            .all()
        )

    @staticmethod
    def top_publishers(limit: int = 10) -> list[tuple[str, int]]:
        rows = (
            db.session.query(BookResult.publisher, func.count(BookResult.id))
            .filter(BookResult.publisher.isnot(None))
            .filter(BookResult.publisher != "")
            .group_by(BookResult.publisher)
            .order_by(func.count(BookResult.id).desc())
            .limit(limit)
            .all()
        )
        return [(p, int(c)) for p, c in rows]
