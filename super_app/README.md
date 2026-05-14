# Super App · 全能 Flask 整合站

> 一站整合 `book`、`calendar`、`calories`、`cs`(課本摘要)、`vibespec-generator` 五大子專案的**真實實作**,
> 不再是樣板資料 ——
> - 📚 **博客來書籍搜尋**:`Playwright` 真實爬蟲
> - 📅 **行事曆 + 會議室預約**:含衝突檢查、管理員核准/駁回
> - 🍱 **卡路里 AI 辨識**:`Google Gemini` Vision 模型分析食物影像
> - 📖 **課本單元摘要**:`Gemini` REST API 產生繁中重點整理
> - 💡 **Vibe Spec 產生器**:把點子轉成 Markdown 技術規格書

---

## 🏗 架構

嚴格 **4 層分離**(Model / Repository / Service / Controller),
Web API 與 MVC View Page 兩種 Controller 各自獨立。

```
app/
├── __init__.py            # App Factory + Blueprint 註冊
├── config.py              # 從 .env 載入設定
├── extensions.py          # SQLAlchemy
├── models/                # Model:Database 結構
│   ├── book_record.py
│   ├── calendar_event.py
│   ├── calorie_record.py
│   ├── summary_record.py
│   └── vibespec_record.py
├── repositories/          # Repository:資料存取(只跟 db 對話)
├── services/              # Service:商業邏輯(呼叫 Gemini、Playwright)
│   ├── book_service.py
│   ├── calendar_service.py
│   ├── calorie_service.py
│   ├── summary_service.py
│   └── vibespec_service.py
├── controllers/           # MVC View Controller(回傳 HTML)
├── api/                   # Web API Controller(回傳 JSON)
├── templates/             # Jinja2 + Vue 3 + Bootstrap 5.3
└── static/
    ├── css/style.css      # Hero 風格自訂樣式
    └── vendor/            # 完全離線:Bootstrap / Vue / Axios / SweetAlert2
```

## 🛠 技術棧

| 層級 | 技術 |
|------|------|
| 後端 | Flask 3 · Flask-SQLAlchemy 3 · SQLite |
| 前端 | Bootstrap 5.3.3 · Vue 3.4 (CDN-Free) · Axios 1.7 · SweetAlert2 11 |
| 爬蟲 | Playwright (Chromium) |
| AI   | Google Gemini API (`google-generativeai` + REST) |
| 影像 | Pillow |

---

## 🚀 快速啟動

### 1. 建立虛擬環境並安裝依賴

```bash
cd super_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 設定環境變數

複製 `.env.example` 為 `.env`,填入 Gemini API Key:

```bash
cp .env.example .env
# 編輯 .env 後填入:
# GEMINI_API_KEY=AIza...
```

### 3. 下載 Playwright Chromium(只需執行一次)

```bash
playwright install chromium
```

> 若已透過 `pip install -r requirements.txt` 安裝 playwright,
> 仍需執行此指令以下載對應的 Chromium 二進位。

### 4. 下載前端離線資產(只需執行一次)

```bash
python scripts/download_assets.py
```

### 5. 啟動

```bash
python run.py
```

開啟瀏覽器 → http://127.0.0.1:**5005**/

---

## 📡 主要 API

| Method | Path | 說明 |
|--------|------|------|
| `POST` | `/api/book/search` | `{keyword}` Playwright 爬博客來 |
| `GET`  | `/api/book/history` | 搜尋歷史 |
| `GET`  | `/api/book/queries/<id>` | 詳細結果 |
| `GET`  | `/api/book/stats` | 熱門關鍵字 / 出版社統計 |
| `GET`  | `/api/calendar/events` | 取得所有事件 |
| `POST` | `/api/calendar/events` | 建立事件(自動衝突檢查) |
| `DELETE` | `/api/calendar/events/<id>` | 刪除 |
| `GET`  | `/api/calendar/bookings/pending` | 待審核會議預約 |
| `PUT`  | `/api/calendar/bookings/<id>/approve` | 核准預約 |
| `PUT`  | `/api/calendar/bookings/<id>/reject` | 駁回預約 |
| `GET/POST` | `/api/calendar/rooms` | 會議廳清單 / 新增 |
| `POST` | `/api/calories/analyze` | `multipart image` Gemini 分析 |
| `GET`  | `/api/calories/analyses` | 分析歷史 |
| `DELETE` | `/api/calories/analyses/<id>` | 刪除 |
| `POST` | `/api/summary/generate` | `{keyword}` 產生課本摘要 |
| `POST` | `/api/vibespec/generate` | `{idea, tech_stack}` 產生 Spec |

---

## 🧪 測試

```bash
python -m pytest
```

外部依賴(Playwright / Gemini)在測試裡使用 `monkeypatch` 隔離,**無需網路**。

預期結果:**15 passed**。

---

## 🎨 設計風格

- **Hero**:每個模組有專屬漸層
  - 書籍 → 藍綠(`#4facfe → #00f2fe`)
  - 行事曆 → 翠綠(`#11998e → #38ef7d`)
  - 卡路里 → 粉橘(`#ff9a9e → #fad0c4`)
  - 摘要 → 紫藍(`#6a11cb → #2575fc`)
  - Vibe Spec → 桃紅橘(`#ee0979 → #ff6a00`)
- 全站使用 Vue 3 `delimiters: ['[[', ']]']` 避開 Jinja 衝突。
- 所有 AJAX 透過 Axios,訊息提示透過 SweetAlert2。

---

## 📦 環境變數

| 變數 | 預設 | 說明 |
|------|------|------|
| `GEMINI_API_KEY` | (必填) | Google AI Studio API Key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | 文字模型 |
| `GEMINI_VISION_MODEL` | `gemini-2.0-flash` | 影像模型 |
| `PLAYWRIGHT_HEADLESS` | `1` | 爬蟲是否無頭 |
| `SCRAPE_TIMEOUT_MS` | `20000` | 爬蟲逾時 |
| `SCRAPE_MAX_RESULTS` | `20` | 最大筆數 |
| `SCRAPE_DETAIL_LIMIT` | `5` | 抓取書籍內容介紹的前 N 本 |
