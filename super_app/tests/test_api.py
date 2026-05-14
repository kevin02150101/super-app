"""針對所有 Web API 端點的煙霧測試。

對外部依賴(Playwright 爬蟲、Gemini API)以 monkeypatch 進行隔離,
確保測試不需網路。
"""
from __future__ import annotations

import io
from datetime import datetime

import pytest

from app.services import book_service, calorie_service, summary_service, vibespec_service


# ---------- Home / Pages ----------
def test_home_loads(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Super App".encode() in r.data


@pytest.mark.parametrize("path", ["/book/", "/calendar/", "/calories/", "/summary/", "/vibespec/"])
def test_module_pages_load(client, path):
    r = client.get(path)
    assert r.status_code == 200


# ---------- Book API (mock Playwright) ----------
def test_book_search_and_history(client, monkeypatch):
    def fake_search(self, keyword):
        from app.models.book_record import BookResult, SearchQuery
        from app.repositories.book_repository import (
            BookResultRepository,
            SearchQueryRepository,
        )

        sq = SearchQuery(keyword=keyword, result_count=1, duration_ms=10, source="mock")
        SearchQueryRepository.add(sq)
        BookResultRepository.add_many(
            [
                BookResult(
                    query_id=sq.id,
                    title=f"{keyword} 入門",
                    authors="作者A",
                    publisher="測試出版社",
                    price=350,
                    image_url="",
                    product_url="https://example.com/b/1",
                )
            ]
        )
        return {
            "query": sq.to_dict(),
            "results": [
                {"title": f"{keyword} 入門", "authors": "作者A", "publisher": "測試出版社"}
            ],
        }

    monkeypatch.setattr(book_service.BookSearchService, "search", fake_search)

    r = client.post("/api/book/search", json={"keyword": "Python"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["success"] is True
    assert len(body["data"]["results"]) == 1

    r2 = client.get("/api/book/history")
    assert r2.status_code == 200
    assert len(r2.get_json()["data"]) >= 1


def test_book_search_empty_keyword(client):
    r = client.post("/api/book/search", json={"keyword": "  "})
    assert r.status_code == 400


# ---------- Calendar API (real, no external deps) ----------
def test_calendar_general_event_crud(client):
    r = client.post(
        "/api/calendar/events",
        json={
            "title": "週會",
            "event_type": "general",
            "start_time": "2026-05-12T10:00",
            "end_time": "2026-05-12T11:00",
        },
    )
    assert r.status_code == 200, r.get_json()
    eid = r.get_json()["data"]["id"]

    r2 = client.get("/api/calendar/events")
    assert r2.status_code == 200
    assert any(e["id"] == eid for e in r2.get_json()["data"])

    r3 = client.delete(f"/api/calendar/events/{eid}")
    assert r3.status_code == 200


def test_calendar_invalid_time(client):
    r = client.post(
        "/api/calendar/events",
        json={
            "title": "X",
            "event_type": "general",
            "start_time": "2026-05-12T10:00",
            "end_time": "2026-05-12T09:00",
        },
    )
    assert r.status_code == 400


def test_calendar_meeting_booking_flow(client):
    r = client.post(
        "/api/calendar/rooms",
        json={"name": "Room A", "location": "3F", "capacity": 8},
    )
    assert r.status_code == 200
    room_id = r.get_json()["data"]["id"]

    r2 = client.post(
        "/api/calendar/events",
        json={
            "title": "與客戶會議",
            "event_type": "meeting",
            "meeting_room_id": room_id,
            "start_time": "2026-06-01T09:00",
            "end_time": "2026-06-01T10:00",
        },
    )
    assert r2.status_code == 200
    eid = r2.get_json()["data"]["id"]
    assert r2.get_json()["data"]["status"] == "pending"

    # 衝突檢查
    r_conflict = client.post(
        "/api/calendar/events",
        json={
            "title": "衝突會議",
            "event_type": "meeting",
            "meeting_room_id": room_id,
            "start_time": "2026-06-01T09:30",
            "end_time": "2026-06-01T10:30",
        },
    )
    assert r_conflict.status_code == 400

    r_app = client.put(f"/api/calendar/bookings/{eid}/approve", json={})
    assert r_app.status_code == 200
    assert r_app.get_json()["data"]["status"] == "approved"


# ---------- Calorie API (mock Gemini) ----------
def test_calorie_analyze(client, monkeypatch):
    def fake_analyze(cls, image_bytes, mime="image/jpeg"):
        return {
            "items": [
                {
                    "name": "雞胸肉",
                    "category": "蛋白質",
                    "calories": 165,
                    "protein_g": 31,
                    "fat_g": 3.6,
                    "carbs_g": 0,
                    "confidence": 0.92,
                }
            ],
            "total_calories": 165,
            "summary": "高蛋白餐點",
            "health_advice": "搭配蔬菜更均衡",
        }

    monkeypatch.setattr(
        calorie_service.AIService, "analyze_food", classmethod(fake_analyze)
    )
    # 以 PIL 產生一張 1x1 JPEG
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color=(255, 0, 0)).save(buf, format="JPEG")
    buf.seek(0)

    r = client.post(
        "/api/calories/analyze",
        data={"image": (buf, "test.jpg")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 200, r.get_json()
    data = r.get_json()["data"]
    assert data["total_calories"] == 165
    assert data["items"][0]["name"] == "雞胸肉"

    r2 = client.get("/api/calories/analyses")
    assert r2.status_code == 200
    assert len(r2.get_json()["data"]) >= 1


# ---------- Summary API (mock Gemini REST) ----------
def test_summary_generate(client, monkeypatch, app):
    app.config["GEMINI_API_KEY"] = "fake"

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "candidates": [
                    {"content": {"parts": [{"text": "## 光合作用\n這是測試摘要"}]}}
                ]
            }

    monkeypatch.setattr(
        summary_service.requests, "post", lambda *a, **k: FakeResp()
    )
    r = client.post("/api/summary/generate", json={"keyword": "光合作用"})
    assert r.status_code == 200, r.get_json()
    assert "光合作用" in r.get_json()["data"]["summary_text"]


def test_summary_validation(client):
    r = client.post("/api/summary/generate", json={"keyword": ""})
    assert r.status_code == 400


# ---------- VibeSpec API (mock Gemini REST) ----------
def test_vibespec_generate(client, monkeypatch, app):
    app.config["GEMINI_API_KEY"] = "fake"

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "candidates": [
                    {"content": {"parts": [{"text": "# 技術規格書\n## 1. 願景\n..."}]}}
                ]
            }

    monkeypatch.setattr(
        vibespec_service.requests, "post", lambda *a, **k: FakeResp()
    )
    r = client.post(
        "/api/vibespec/generate", json={"idea": "做一個 AI 食譜推薦"}
    )
    assert r.status_code == 200, r.get_json()
    assert "技術規格書" in r.get_json()["data"]["spec_markdown"]
