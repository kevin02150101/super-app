"""Controller 整合測試:以 monkeypatch 替換掉 Playwright 爬蟲。"""
from app.services.book_search_service import ScrapedBook
from app.controllers.api import book_api_controller as bookmod


def _fake_search(self, keyword, max_results=None):
    return [
        ScrapedBook(title=f"《{keyword}》入門", authors="某作者", publisher="某出版社",
                    published_at="2024", price=399,
                    image_url="http://x/i.jpg", product_url="http://x/p"),
    ]


def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"BookFinder" in resp.data


def test_history_page(client):
    assert client.get("/history/").status_code == 200


def test_dashboard_page(client):
    assert client.get("/dashboard/").status_code == 200


def test_api_search_records_empty(client):
    resp = client.get("/api/v1/search-records")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"] == []


def test_api_books_search_validates_keyword(client):
    resp = client.post("/api/v1/books/search", json={"keyword": ""})
    assert resp.status_code == 400


def test_api_books_search_with_fake_scraper(client, monkeypatch):
    from app.services.book_search_service import BookSearchService
    monkeypatch.setattr(BookSearchService, "search", _fake_search)

    # 重新綁定 service 內部的 scraper(它在 import 時已建立)
    bookmod._service.scraper = BookSearchService()

    resp = client.post("/api/v1/books/search", json={"keyword": "Flask"})
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["query"]["keyword"] == "Flask"
    assert len(body["data"]["results"]) == 1

    # history 應有一筆
    rec = client.get("/api/v1/search-records").get_json()
    assert len(rec["data"]) == 1

    qid = rec["data"][0]["id"]
    detail = client.get(f"/api/v1/search-records/{qid}").get_json()
    assert detail["success"] is True
    assert detail["data"]["results"][0]["title"].startswith("《Flask》")

    # dashboard
    stats = client.get("/api/v1/stats/dashboard").get_json()
    assert stats["data"]["overview"]["total_queries"] == 1
