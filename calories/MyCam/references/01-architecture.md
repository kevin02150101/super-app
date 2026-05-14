# 01 — 系統架構與資料流

## 1. 高層架構

```
[Browser]
  │  (Jinja2 渲染 + Vue 3 SPA-like 互動)
  ▼
┌───────────────────────────────────────────┐
│              Flask Application            │
│ ┌────────────────┐   ┌──────────────────┐ │
│ │  MVC (View)    │   │   Web API        │ │
│ │  Controllers   │   │   /api/*         │ │
│ └────────┬───────┘   └────────┬─────────┘ │
│          │  呼叫              │           │
│          ▼                    ▼           │
│ ┌────────────────────────────────────────┐│
│ │           Service Layer                ││
│ │  AuthService  AnalysisService          ││
│ │  AIService(Gemini)  ImageService       ││
│ │  StatsService                          ││
│ └────────────────┬───────────────────────┘│
│                  ▼                        │
│ ┌────────────────────────────────────────┐│
│ │         Repository Layer               ││
│ │ UserRepo AnalysisRepo FoodItemRepo     ││
│ └────────────────┬───────────────────────┘│
│                  ▼                        │
│            SQLAlchemy / SQLite            │
└───────────────────────────────────────────┘

外部：Google Gemini API (HTTPS)
```

## 2. 請求資料流範例：影像分析

1. 前端（Vue 元件 `CaptureUploader.vue`）→ `POST /api/analyze`（multipart 影像）。
2. API 層驗證 Session、檢查 MIME / 大小。
3. 呼叫 `AnalysisService.analyze(user_id, image_bytes)`。
4. `ImageService.preprocess()` 進行壓縮、Resize、Base64。
5. `AIService.analyze_food(image)` → Google Gemini API。
6. 解析 JSON 回應 → 組裝為 `Analysis` 與 `FoodItem` 實體。
7. `AnalysisRepository.create()` / `FoodItemRepository.bulk_create()` 寫入 SQLite。
8. API 回傳 Dashboard 卡片資料給前端 → SweetAlert2 顯示成功 → 跳轉 `/history/<id>`。

## 3. 分層職責邊界

| 層 | 可呼叫 | 禁止 |
|---|---|---|
| Controller / API | Service | 直接讀寫 DB、直接呼叫 Gemini |
| Service | Repository, 外部 API | 直接渲染 HTML、操作 request |
| Repository | SQLAlchemy Session | 任何業務邏輯（驗證、計算 KPI 等） |
| AI Service | Gemini SDK | 寫資料庫 |

## 4. 設計原則

- 單向依賴：Controller → Service → Repository。
- DTO/Pydantic schema 在 Service 與 API 之間傳遞。
- 例外集中於 `app/errors.py`，由 Flask `errorhandler` 統一輸出。
- 設定集中於 `config.py`，由 `.env` 注入。
