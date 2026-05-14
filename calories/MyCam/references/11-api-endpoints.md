# 11 — API Endpoint 規格

> 所有回應統一使用 `{ ok, data | error }` 格式。
> 除註冊/登入外，皆需登入（Session Cookie）。

## 1. Auth

### POST /api/auth/register
Req：
```json
{ "email": "a@b.com", "password": "xxxx", "nickname": "Ray" }
```
Res 201：
```json
{ "ok": true, "data": { "id": 1, "email": "a@b.com", "nickname": "Ray" } }
```

### POST /api/auth/login
Req：`{ "email": "...", "password": "..." }`
Res 200：`{ "ok": true, "data": { "id": 1, "nickname": "Ray" } }`

### POST /api/auth/logout
Res 200：`{ "ok": true }`

## 2. Analyze

### POST /api/analyze  (multipart/form-data)
Field：`image` (file)
Res 201：
```json
{
  "ok": true,
  "data": {
    "id": 12,
    "image_path": "/static/uploads/1/abc.jpg",
    "total_calories": 540,
    "summary": "...",
    "health_advice": "...",
    "analyzed_at": "2026-05-11T08:30:00",
    "items": [
      { "name": "雞胸肉", "category": "蛋白質", "calories": 180, "confidence": 0.92 }
    ]
  }
}
```
錯誤：`NO_FILE` / `BAD_MIME` / `TOO_LARGE` / `AI_FAIL`

## 3. Analyses

### GET /api/analyses?page=1&per_page=20
Res：
```json
{
  "ok": true,
  "data": {
    "items": [ { "id": 12, "total_calories": 540, "analyzed_at": "...", "thumb": "...", "main_food": "雞胸肉" } ],
    "page": 1, "per_page": 20, "total": 35
  }
}
```

### GET /api/analyses/<id>
Res：同 POST /api/analyze 的 `data`。

### DELETE /api/analyses/<id>
Res：`{ "ok": true }`，錯：`NOT_FOUND` / `FORBIDDEN`。

## 4. Stats

### GET /api/stats/summary
```json
{
  "ok": true,
  "data": {
    "today_calories": 1340,
    "total_count": 87,
    "top_food": "雞胸肉",
    "avg_daily_7d": 1620
  }
}
```

### GET /api/stats/calories?days=30
```json
{ "ok": true, "data": [ { "date": "2026-04-12", "calories": 1480 } ] }
```

### GET /api/stats/categories
```json
{
  "ok": true,
  "data": [
    { "category": "主食",   "count": 30, "calories": 5400 },
    { "category": "蛋白質", "count": 22, "calories": 3960 }
  ]
}
```

## 5. 錯誤碼總表

| Code | HTTP | 說明 |
|---|---|---|
| `UNAUTHORIZED` | 401 | 未登入 |
| `FORBIDDEN` | 403 | 越權 |
| `NOT_FOUND` | 404 | 資源不存在 |
| `NO_FILE` | 400 | 缺檔案 |
| `BAD_MIME` | 400 | 非影像 |
| `TOO_LARGE` | 413 | 超過 MAX_UPLOAD_MB |
| `AI_NO_KEY` | 500 | 未設定 GEMINI_API_KEY |
| `AI_FAIL` | 502 | Gemini 失敗 |
| `AI_BAD_JSON` | 502 | Gemini 回應非合法 JSON |
| `RATE_LIMIT` | 429 | 觸發速率限制 |
