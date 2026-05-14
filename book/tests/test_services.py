import pytest

from app.services.book_search_service import ScrapedBook
from app.services.search_record_service import SearchRecordService
from app.services.stats_service import StatsService


class FakeScraper:
    def __init__(self, books):
        self.books = books
        self.calls = []

    def search(self, keyword, max_results=None):
        self.calls.append(keyword)
        return list(self.books)


def test_search_and_store_persists_query_and_results(app):
    scraper = FakeScraper([
        ScrapedBook(title="原子習慣", authors="James Clear", publisher="方智",
                    published_at="2019", price=320,
                    image_url="https://x/img.jpg", product_url="https://x/p"),
        ScrapedBook(title="深度學習", authors="Goodfellow", publisher="碁峰",
                    published_at="2018", price=900,
                    image_url=None, product_url=None),
    ])
    service = SearchRecordService(scraper=scraper)
    out = service.search_and_store("習慣")

    assert out["query"]["keyword"] == "習慣"
    assert out["query"]["result_count"] == 2
    assert len(out["results"]) == 2
    assert scraper.calls == ["習慣"]
    # 新增:summary 與分類欄位
    assert "summary" in out
    assert out["summary"]["stats"]["total"] == 2
    assert out["query"]["primary_category"]
    assert all(r["category"] for r in out["results"])

    detail = service.get_detail(out["query"]["id"])
    assert detail is not None
    assert {r["title"] for r in detail["results"]} == {"原子習慣", "深度學習"}
    assert detail["query"]["summary_text"]


def test_search_and_store_rejects_blank(app):
    service = SearchRecordService(scraper=FakeScraper([]))
    with pytest.raises(ValueError):
        service.search_and_store("   ")


def test_stats_overview(app):
    scraper = FakeScraper([
        ScrapedBook("A", None, "甲", None, 100, None, None),
        ScrapedBook("B", None, "甲", None, 200, None, None),
    ])
    rec = SearchRecordService(scraper=scraper)
    rec.search_and_store("k1")
    rec.search_and_store("k1")
    rec.search_and_store("k2")

    stats = StatsService().dashboard()
    assert stats["overview"]["total_queries"] == 3
    assert stats["overview"]["distinct_keywords"] == 2
    assert stats["overview"]["total_results"] == 6
    assert stats["top_keywords"][0]["keyword"] == "k1"
    assert stats["top_publishers"][0]["publisher"] == "甲"
    assert isinstance(stats["daily_trend"], list)
