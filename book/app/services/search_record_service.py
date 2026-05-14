"""Search-record service — orchestrates the scraper and repository for business logic and storage."""
from __future__ import annotations

import time

from app.models.book_result import BookResult
from app.models.search_query import SearchQuery
from app.repositories.book_result_repository import BookResultRepository
from app.repositories.search_query_repository import SearchQueryRepository
from app.services.book_search_service import BookSearchService, ScrapedBook
from app.services.summary_service import SummaryService


class SearchRecordService:
    def __init__(
        self,
        query_repo: SearchQueryRepository | None = None,
        result_repo: BookResultRepository | None = None,
        scraper: BookSearchService | None = None,
        summary_service: SummaryService | None = None,
    ):
        self.query_repo = query_repo or SearchQueryRepository()
        self.result_repo = result_repo or BookResultRepository()
        self.scraper = scraper or BookSearchService()
        self.summary_service = summary_service or SummaryService()

    def search_and_store(self, keyword: str) -> dict:
        keyword = (keyword or "").strip()
        if not keyword:
            raise ValueError("Keyword can't be empty")

        started = time.perf_counter()
        scraped: list[ScrapedBook] = self.scraper.search(keyword)
        duration_ms = int((time.perf_counter() - started) * 1000)

        # Category + summary
        categories = self.summary_service.classify_many(scraped, fallback_keyword=keyword)
        summary = self.summary_service.summarize(keyword, scraped, categories)

        query = SearchQuery(
            keyword=keyword,
            result_count=len(scraped),
            duration_ms=duration_ms,
            source="books.com.tw",
            primary_category=summary["stats"]["primary_category"],
            summary_text=summary["text"],
        )
        self.query_repo.add(query)

        results = [
            BookResult(
                query_id=query.id,
                title=b.title[:500],
                authors=(b.authors or "")[:500] or None,
                publisher=(b.publisher or "")[:200] or None,
                published_at=(b.published_at or "")[:50] or None,
                price=b.price,
                image_url=b.image_url,
                product_url=b.product_url,
                category=cat,
                description=getattr(b, "description", None),
                summary=self.summary_service.summarize_text(
                    getattr(b, "description", None)
                ),
            )
            for b, cat in zip(scraped, categories)
        ]
        if results:
            self.result_repo.add_many(results)

        return {
            "query": query.to_dict(),
            "results": [r.to_dict() for r in results],
            "summary": summary,
        }

    def list_recent(self, limit: int = 50, category: str | None = None) -> list[dict]:
        rows = self.query_repo.find_recent(limit=limit, category=category)
        return [r.to_dict() for r in rows]

    def search_history(
        self, keyword: str, limit: int = 50, category: str | None = None
    ) -> list[dict]:
        rows = self.query_repo.search_by_keyword(keyword, limit=limit, category=category)
        return [r.to_dict() for r in rows]

    def get_detail(self, query_id: int) -> dict | None:
        query = self.query_repo.find_by_id(query_id)
        if query is None:
            return None
        results = self.result_repo.find_by_query_id(query_id)
        return {
            "query": query.to_dict(),
            "results": [r.to_dict() for r in results],
        }

    def list_categories(self) -> list[str]:
        return self.query_repo.list_categories()

    def delete(self, query_id: int) -> bool:
        return self.query_repo.delete(query_id)
