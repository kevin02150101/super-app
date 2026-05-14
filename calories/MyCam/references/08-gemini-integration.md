# 08 — Gemini API 整合

> **嚴格限制**：不可使用 Ollama、不可使用地端 `gemma4:e2b` 或任何地端模型。
> 僅能使用 Google Gemini Cloud API，透過 `.env` 中的 `GEMINI_API_KEY`。

## 1. 套件

```
google-generativeai>=0.8.0
python-dotenv>=1.0.0
```

## 2. .env 範本

```
FLASK_ENV=development
SECRET_KEY=change-me
DATABASE_URL=sqlite:///instance/mycam.db
GEMINI_API_KEY=YOUR_API_KEY_HERE
GEMINI_MODEL=gemini-2.5-flash
MAX_UPLOAD_MB=8
```

## 3. AIService 實作骨架

```python
# services/ai_service.py
import os, json, base64
import google.generativeai as genai
from app.errors import MyCamError

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":      {"type": "string"},
                    "category":  {"type": "string"},
                    "calories":  {"type": "number"},
                    "protein_g": {"type": "number"},
                    "fat_g":     {"type": "number"},
                    "carbs_g":   {"type": "number"},
                    "confidence":{"type": "number"}
                },
                "required": ["name", "calories"]
            }
        },
        "total_calories": {"type": "number"},
        "summary":        {"type": "string"},
        "health_advice":  {"type": "string"}
    },
    "required": ["items", "total_calories", "summary", "health_advice"]
}

_PROMPT = """你是專業營養師與食物影像辨識專家。
請辨識影像中的食物，估算各品項卡路里與營養素，
並提供整體健康建議。請**只**以指定 JSON Schema 回傳，不要任何其他文字。"""

class AIService:
    _configured = False

    @classmethod
    def _ensure(cls):
        if cls._configured:
            return
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise MyCamError("AI_NO_KEY", "未設定 GEMINI_API_KEY", 500)
        genai.configure(api_key=api_key)
        cls._configured = True

    @classmethod
    def analyze_food(cls, image_bytes: bytes, mime: str = "image/jpeg") -> dict:
        cls._ensure()
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        try:
            resp = model.generate_content(
                [
                    _PROMPT,
                    {"mime_type": mime, "data": image_bytes},
                ],
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": _RESPONSE_SCHEMA,
                    "temperature": 0.2,
                },
            )
            return json.loads(resp.text)
        except Exception as e:
            raise MyCamError("AI_FAIL", f"Gemini 分析失敗: {e}", 502)
```

## 4. 回應 JSON 範例

```json
{
  "items": [
    {"name": "雞胸肉", "category": "蛋白質", "calories": 180, "protein_g": 33, "fat_g": 4, "carbs_g": 0, "confidence": 0.92},
    {"name": "糙米飯", "category": "主食",   "calories": 220, "protein_g": 5,  "fat_g": 2, "carbs_g": 46,"confidence": 0.88}
  ],
  "total_calories": 400,
  "summary": "高蛋白低脂組合，碳水適中。",
  "health_advice": "建議搭配深色蔬菜以補足纖維與微量營養素。"
}
```

## 5. 錯誤處理

| 代碼 | 情境 |
|---|---|
| `AI_NO_KEY` | 缺 API Key |
| `AI_FAIL`   | Gemini 拋例外 / 逾時 |
| `AI_BAD_JSON` | 解析失敗（回退：以正則救援後再次解析） |

## 6. 禁止事項（明文）

- ❌ 不得 `import ollama`。
- ❌ 不得使用 `gemma4:e2b`、`llama`、`mistral` 等地端模型。
- ❌ 不得在 `.env` 之外硬編碼任何 Key。
- ❌ Controller / Repository / 前端 JS **不得**直接呼叫 Gemini。
