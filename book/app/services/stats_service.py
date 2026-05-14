"""統計分析服務:供儀表板使用。"""
from __future__ import annotations

from app.repositories.book_result_repository import BookResultRepository
from app.repositories.search_query_repository import SearchQueryRepository


class StatsService:
    def __init__(
        self,
        query_repo: SearchQueryRepository | None = None,
        result_repo: BookResultRepository | None = None,
    ):
        self.query_repo = query_repo or SearchQueryRepository()
        self.result_repo = result_repo or BookResultRepository()

    def overview(self) -> dict:
        return {
            "total_queries": self.query_repo.count_total(),
            "distinct_keywords": self.query_repo.count_distinct_keywords(),
            "total_results": self.result_repo.count_total(),
            "avg_results_per_query": round(self.query_repo.avg_result_count(), 2),
            "avg_book_price": round(self.result_repo.avg_price(), 2),
        }

    def top_keywords(self, limit: int = 10) -> list[dict]:
        return [
            {"keyword": k, "count": c}
            for k, c in self.query_repo.top_keywords(limit=limit)
        ]

    def top_publishers(self, limit: int = 10) -> list[dict]:
        return [
            {"publisher": p, "count": c}
            for p, c in self.result_repo.top_publishers(limit=limit)
        ]

    def daily_trend(self, days: int = 14) -> list[dict]:
        return [{"date": d, "count": c} for d, c in self.query_repo.daily_counts(days)]

    def category_distribution(self) -> list[dict]:
        return [
            {"category": c, "count": n}
            for c, n in self.query_repo.category_distribution()
        ]

    def book_category_distribution(self) -> list[dict]:
        return [
            {"category": c, "count": n}
            for c, n in self.result_repo.category_distribution()
        ]

    def dashboard(self) -> dict:
        return {
            "overview": self.overview(),
            "top_keywords": self.top_keywords(),
            "top_publishers": self.top_publishers(),
            "daily_trend": self.daily_trend(),
            "query_categories": self.category_distribution(),
            "book_categories": self.book_category_distribution(),
        }
