from datetime import datetime, timedelta

from sqlalchemy import func

from app.extensions import db
from app.models.search_query import SearchQuery


class SearchQueryRepository:
    def add(self, query: SearchQuery) -> SearchQuery:
        db.session.add(query)
        db.session.commit()
        return query

    def find_by_id(self, query_id: int) -> SearchQuery | None:
        return db.session.get(SearchQuery, query_id)

    def find_recent(
        self, limit: int = 50, category: str | None = None
    ) -> list[SearchQuery]:
        q = SearchQuery.query
        if category:
            q = q.filter(SearchQuery.primary_category == category)
        return q.order_by(SearchQuery.created_at.desc()).limit(limit).all()

    def search_by_keyword(
        self, keyword: str, limit: int = 50, category: str | None = None
    ) -> list[SearchQuery]:
        like = f"%{keyword}%"
        q = SearchQuery.query.filter(SearchQuery.keyword.ilike(like))
        if category:
            q = q.filter(SearchQuery.primary_category == category)
        return q.order_by(SearchQuery.created_at.desc()).limit(limit).all()

    def delete(self, query_id: int) -> bool:
        obj = self.find_by_id(query_id)
        if obj is None:
            return False
        db.session.delete(obj)
        db.session.commit()
        return True

    # ----- 統計分析 -----
    def count_total(self) -> int:
        return db.session.query(func.count(SearchQuery.id)).scalar() or 0

    def count_distinct_keywords(self) -> int:
        return (
            db.session.query(func.count(func.distinct(SearchQuery.keyword))).scalar()
            or 0
        )

    def top_keywords(self, limit: int = 10) -> list[tuple[str, int]]:
        rows = (
            db.session.query(SearchQuery.keyword, func.count(SearchQuery.id))
            .group_by(SearchQuery.keyword)
            .order_by(func.count(SearchQuery.id).desc())
            .limit(limit)
            .all()
        )
        return [(r[0], int(r[1])) for r in rows]

    def daily_counts(self, days: int = 14) -> list[tuple[str, int]]:
        since = datetime.utcnow() - timedelta(days=days - 1)
        date_expr = func.strftime("%Y-%m-%d", SearchQuery.created_at)
        rows = (
            db.session.query(date_expr.label("d"), func.count(SearchQuery.id))
            .filter(SearchQuery.created_at >= since)
            .group_by("d")
            .order_by("d")
            .all()
        )
        return [(r[0], int(r[1])) for r in rows]

    def avg_result_count(self) -> float:
        v = db.session.query(func.avg(SearchQuery.result_count)).scalar()
        return float(v) if v is not None else 0.0

    def list_categories(self) -> list[str]:
        rows = (
            db.session.query(SearchQuery.primary_category)
            .filter(SearchQuery.primary_category.isnot(None))
            .filter(SearchQuery.primary_category != "")
            .distinct()
            .order_by(SearchQuery.primary_category.asc())
            .all()
        )
        return [r[0] for r in rows]

    def category_distribution(self) -> list[tuple[str, int]]:
        rows = (
            db.session.query(SearchQuery.primary_category, func.count(SearchQuery.id))
            .filter(SearchQuery.primary_category.isnot(None))
            .group_by(SearchQuery.primary_category)
            .order_by(func.count(SearchQuery.id).desc())
            .all()
        )
        return [(r[0], int(r[1])) for r in rows]
