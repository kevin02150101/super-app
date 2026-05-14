import io
from unittest.mock import patch
from PIL import Image


def _png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), (200, 50, 50)).save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_analyze_with_mocked_gemini(client):
    client.post("/api/auth/register", json={"email": "x@y.com", "password": "secret123"})

    fake = {
        "items": [{"name": "Apple", "category": "Fruit", "calories": 95, "confidence": 0.9}],
        "total_calories": 95,
        "summary": "A medium-sized apple.",
        "health_advice": "Pairs well with protein.",
    }
    with patch("services.ai_service.AIService.analyze_food", return_value=fake):
        data = {"image": (_png_bytes(), "a.png", "image/png")}
        r = client.post("/api/analyze", data=data, content_type="multipart/form-data")
        assert r.status_code == 201, r.get_data(as_text=True)
        body = r.get_json()
        assert body["ok"] is True
        assert body["data"]["total_calories"] == 95
        assert len(body["data"]["items"]) == 1
        assert body["data"]["items"][0]["name"] == "Apple"


def test_history_after_analyze(client):
    client.post("/api/auth/register", json={"email": "h@h.com", "password": "secret123"})
    fake = {"items": [], "total_calories": 0, "summary": "None", "health_advice": "—"}
    with patch("services.ai_service.AIService.analyze_food", return_value=fake):
        client.post("/api/analyze",
                    data={"image": (_png_bytes(), "a.png", "image/png")},
                    content_type="multipart/form-data")

    r = client.get("/api/analyses")
    assert r.status_code == 200
    body = r.get_json()
    assert body["data"]["total"] == 1
