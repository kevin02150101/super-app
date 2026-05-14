# 16 — 測試方式

## 1. 測試框架

- `pytest`、`pytest-flask`（可選）。
- 使用獨立 SQLite：`sqlite:///:memory:` 或 `instance/test.db`。

## 2. 結構

```
tests/
├── conftest.py        # Flask app fixture、db fixture、登入 client
├── test_auth.py
├── test_analysis.py
├── test_ai_service.py # Mock Gemini
├── test_repository.py
└── test_api.py
```

## 3. Gemini Mock 範例

```python
# tests/test_ai_service.py
from unittest.mock import patch
from services.ai_service import AIService

FAKE = {
  "items":[{"name":"雞胸肉","category":"蛋白質","calories":180,"confidence":0.9}],
  "total_calories":180,"summary":"高蛋白","health_advice":"配蔬菜"
}

def test_analyze_food_ok(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    with patch("services.ai_service.genai") as g:
        g.GenerativeModel.return_value.generate_content.return_value.text = '{"items":[{"name":"x","calories":1}],"total_calories":1,"summary":"s","health_advice":"a"}'
        out = AIService.analyze_food(b"\x00", "image/jpeg")
        assert out["total_calories"] == 1
```

## 4. API 測試範例

```python
def test_analyze_requires_login(client):
    resp = client.post("/api/analyze")
    assert resp.status_code == 401
```

## 5. 覆蓋率目標

- Service 層 ≥ 80%。
- API 層所有 endpoint 至少 1 個正向 + 1 個負向。

## 6. 手動驗收清單

- [ ] 註冊 → 登入 → Dashboard 正常顯示
- [ ] 啟動鏡頭可預覽、拍照可分析
- [ ] 上傳 JPG/PNG 可分析
- [ ] 超過 8MB 顯示 SweetAlert 錯誤
- [ ] 未設定 `GEMINI_API_KEY` 顯示 `AI_NO_KEY`
- [ ] 歷史列表分頁、詳情、刪除
- [ ] Dashboard 圖表正確
- [ ] 登出後保護頁重導 `/auth/login`
