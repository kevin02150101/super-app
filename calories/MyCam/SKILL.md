---
name: MyCam
description: |
  MyCam 是一套以 Python Flask 為核心的食物影像分析網站系統。使用者可註冊/登入後，
  透過鏡頭拍攝或上傳相片，系統呼叫 Google Gemini API 進行食物種類辨識、卡路里估算
  與營養分析，並以 Hero Dashboard 風格的儀表板呈現分析結果並存入 SQLite 個人歷史紀錄。
  本 Skill 為核心規格，詳細設計請查閱 references/ 目錄。
version: 1.0.0
language: zh-TW
tags:
  - flask
  - python
  - gemini
  - sqlite
  - bootstrap5
  - vue3
  - dashboard
---

# MyCam — Agent Skills 規格包（核心 SKILL）

> 本檔為「主要 Skill 核心規格」，提供專案總覽、原則與導讀；
> 所有詳細設計（分層、資料表、API、前端範本、部署等）皆切割於 `references/` 之下。

---

## 1. 專案目標

建立一個 Python Flask 網站系統 **MyCam**：

- 提供使用者**註冊 / 登入**功能（Session-based）。
- 登入後可**啟動鏡頭**或**上傳相片**。
- 透過 **Google Gemini API** 進行影像分析：
  - 食物種類辨識
  - 卡路里估算
  - 營養與飲食狀況分析
- 以 **Hero Dashboard 風格**呈現分析結果（卡片式區塊）。
- 分析結果儲存至 **SQLite**，形成個人歷史紀錄。
- 提供歷史查詢、單筆檢視、總體統計、種類統計、Dashboard 圖表分析。

### 重要約束（必須遵守）

- **不可**使用 Ollama。
- **不可**使用任何地端模型（含 `gemma4:e2b` 或其他地端推論）。
- AI 模組**僅能**呼叫 Google Gemini Cloud API。
- API Key 必須透過 `.env` 中的 `GEMINI_API_KEY` 載入，禁止硬編碼。
- AI 邏輯必須封裝為獨立的 **AI Service 模組**（`services/ai_service.py`）。

---

## 2. 系統架構（四層）

```
┌─────────────────────────────────────────────────────┐
│                    Web API 層                       │  /api/*  (JSON)
├─────────────────────────────────────────────────────┤
│                  MVC 層 (Controller/View)           │  Blueprint + Jinja2
├─────────────────────────────────────────────────────┤
│                    Service 層                       │  業務邏輯 / AI Service
├─────────────────────────────────────────────────────┤
│                   Repository 層                     │  資料存取 (SQLite)
└─────────────────────────────────────────────────────┘
```

- **MVC 層**：頁面渲染（Jinja2）與 Controller（Flask Blueprint）。
- **Repository 層**：封裝所有 SQL/ORM 資料存取邏輯。
- **Service 層**：業務邏輯、影像處理、Gemini API 整合。
- **Web API 層**：對前端 Vue 3 提供 JSON API。

> 詳細分層說明：請見 `references/03-mvc-layer.md`、`04-repository-layer.md`、`05-service-layer.md`、`06-web-api-layer.md`。

---

## 3. 技術堆疊

### 後端
- Python 3.11+
- Flask 3.x
- Flask-Login（Session 認證）
- SQLAlchemy + SQLite
- Pillow（影像處理）
- google-generativeai（Gemini SDK）
- python-dotenv

### 前端（地端，View Page 採地端架構，不使用 CDN-only SPA）
- Bootstrap **5.3**
- Vue **3.0**（透過 `<script>` 引入 global build）
- axios
- SweetAlert2
- Chart.js（Dashboard 圖表）

### 風格
- **Hero Dashboard 風格**：頂部 Hero 區（漸層 + 大標題 + KPI）、左側 Sidebar、卡片式內容區。

> 樣板 sample、CSS 範本、前端元件範例：請見 `references/12-view-templates.md`、`13-css-templates.md`、`14-frontend-components.md`。

---

## 4. 資料夾結構（總覽）

```
MyCam/
├── app.py
├── config.py
├── .env.example
├── requirements.txt
├── README.md
├── controllers/        # MVC 層 — Controller（Blueprint）
├── api/                # Web API 層
├── services/           # Service 層（含 ai_service.py）
├── repositories/       # Repository 層
├── models/             # SQLAlchemy Models
├── templates/          # Jinja2 View
├── static/
│   ├── css/
│   ├── js/
│   ├── vendor/         # 地端 bootstrap / vue / axios / sweetalert2 / chart.js
│   └── uploads/
├── tests/
└── instance/
    └── mycam.db
```

> 完整檔案級結構：請見 `references/02-folder-structure.md`。

---

## 5. 資料庫（SQLite）總覽

三張主要資料表：

| 資料表 | 用途 |
|---|---|
| `users` | 使用者帳號 |
| `analyses` | 影像分析紀錄（含 Gemini 結果 JSON） |
| `food_items` | 單筆分析所辨識出的食物明細（可多筆對一） |

> 完整 DDL、欄位、索引、ERD：請見 `references/07-database-schema.md`。

---

## 6. Gemini API 整合（核心原則）

- SDK：`google-generativeai`
- Model：`gemini-2.5-flash`（或 `gemini-2.5-pro`，透過 `.env` 設定）
- 呼叫流程：

```
使用者上傳/拍照 → ImageService（壓縮、轉碼）
                → AIService.analyze_food(image_bytes)
                → Gemini API
                → 回傳結構化 JSON（食物名稱、卡路里、營養、建議）
                → AnalysisService.save() → Repository → SQLite
                → 回傳 Dashboard 卡片資料
```

- **必須**強制 Gemini 以 JSON Schema 回應，避免不可控字串。
- 失敗時回傳統一錯誤碼，前端以 SweetAlert2 提示。

> Prompt 設計、JSON Schema、錯誤處理：請見 `references/08-gemini-integration.md`。

---

## 7. 前端頁面 / Dashboard 規劃（總覽）

頁面清單：

| 路徑 | 說明 |
|---|---|
| `/` | 首頁 Hero Landing |
| `/auth/register` | 註冊 |
| `/auth/login` | 登入 |
| `/dashboard` | Hero Dashboard 主頁（KPI + 圖表） |
| `/capture` | 鏡頭拍攝 / 上傳分析 |
| `/history` | 歷史紀錄列表 |
| `/history/<id>` | 單筆分析詳情 |
| `/stats` | 卡路里 / 食物種類統計 |

> 詳細頁面區塊與 Dashboard UI：請見 `references/09-frontend-pages.md`、`10-dashboard-ui.md`。

---

## 8. API Endpoint 總覽

| Method | Path | 說明 |
|---|---|---|
| POST | `/api/auth/register` | 註冊 |
| POST | `/api/auth/login` | 登入 |
| POST | `/api/auth/logout` | 登出 |
| POST | `/api/analyze` | 上傳影像並分析（multipart） |
| GET  | `/api/analyses` | 歷史列表（分頁） |
| GET  | `/api/analyses/<id>` | 單筆詳情 |
| DELETE | `/api/analyses/<id>` | 刪除 |
| GET  | `/api/stats/summary` | KPI 摘要 |
| GET  | `/api/stats/calories` | 卡路里時序 |
| GET  | `/api/stats/categories` | 食物種類統計 |

> 完整 Request / Response Schema：請見 `references/11-api-endpoints.md`。

---

## 9. references 目錄導讀

| 檔案 | 主題 |
|---|---|
| `references/01-architecture.md` | 系統架構與資料流 |
| `references/02-folder-structure.md` | 完整資料夾與檔案結構 |
| `references/03-mvc-layer.md` | MVC 層設計 |
| `references/04-repository-layer.md` | Repository 層設計 |
| `references/05-service-layer.md` | Service 層設計 |
| `references/06-web-api-layer.md` | Web API 層設計 |
| `references/07-database-schema.md` | SQLite 資料表設計與 DDL |
| `references/08-gemini-integration.md` | Gemini API 整合 / Prompt / Schema |
| `references/09-frontend-pages.md` | 前端頁面規劃 |
| `references/10-dashboard-ui.md` | Hero Dashboard UI 規劃 |
| `references/11-api-endpoints.md` | API Endpoint 規格 |
| `references/12-view-templates.md` | View 樣板 sample |
| `references/13-css-templates.md` | CSS 範本（Hero Dashboard） |
| `references/14-frontend-components.md` | Vue 3 前端元件範例 |
| `references/15-development-steps.md` | 開發步驟 |
| `references/16-testing.md` | 測試方式 |
| `references/17-deployment.md` | 部署與啟動說明 |

---

## 10. Agent 使用此 Skill 的原則

1. 任何 MyCam 相關任務先讀本檔，再依需求 `read` 對應 `references/*.md`。
2. 變更分層職責時，**禁止**讓 Controller 直接存取 SQL；必須走 Service → Repository。
3. 涉及 AI 推論時，**只能**呼叫 `services/ai_service.py`；不得在 Controller / Repository 直接呼叫 Gemini SDK。
4. 前端資源**一律**從 `static/vendor/` 載入（地端），不從 CDN。
5. 新增資料表須同步更新 `references/07-database-schema.md` 與 Repository。
