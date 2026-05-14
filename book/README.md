# BookFinder · 博客來書籍查詢系統

一個 Flask + React + Bootstrap 5.3 的全端示範,符合 [AGENTS.md](AGENTS.md) 規範:

- **Repository / Service / MVC Controller / Web API Controller** 嚴格四層分離。
- **離線前端**(無 CDN):Bootstrap 5.3、React 18、Axios、Babel Standalone 全部本機 `static/` 提供。
- **書名查詢**:後端以 **Playwright** 自動連線博客來搜尋頁,解析結果。
- **卡片式呈現**:RWD Grid + Hero 風格首屏。
- **SQLite** 儲存查詢與結果。
- **歷史紀錄** 與 **統計儀表板**(KPI、熱門關鍵字、熱門出版社、近 14 日趨勢)。

## 快速開始

```powershell
# 1. 建立虛擬環境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. 安裝相依套件
pip install -r requirements.txt
python -m playwright install chromium

# 3. 下載前端離線資源(只需一次)
python scripts\download_assets.py

# 4. 啟動
$env:FLASK_APP = "run.py"
flask run --host=0.0.0.0 --port=5000
# 或: python run.py
```

開啟瀏覽器:<http://localhost:5000>

## 路由總覽

| 類型 | 方法 | 路徑 | 說明 |
|------|------|------|------|
| MVC  | GET  | `/`                              | 首頁(Hero + 查詢) |
| MVC  | GET  | `/history/`                      | 歷史紀錄頁 |
| MVC  | GET  | `/dashboard/`                    | 統計儀表板 |
| API  | POST | `/api/v1/books/search`           | 書名查詢(觸發爬蟲 + 入庫) |
| API  | GET  | `/api/v1/search-records`         | 列出歷史紀錄(支援 `keyword`) |
| API  | GET  | `/api/v1/search-records/<id>`    | 取得單筆紀錄與結果 |
| API  | DEL  | `/api/v1/search-records/<id>`    | 刪除紀錄(連動刪結果) |
| API  | GET  | `/api/v1/stats/dashboard`        | 儀表板數據 |

## 目錄結構

```
app/
├── __init__.py              # App Factory
├── config.py
├── extensions.py            # SQLAlchemy db
├── models/                  # SearchQuery, BookResult
├── repositories/            # 純資料存取
├── services/                # BookSearchService(Playwright)、SearchRecordService、StatsService
├── controllers/
│   ├── mvc/                 # home / history / dashboard
│   └── api/                 # books / search-records / stats
├── templates/               # Jinja2(layout + 各頁)
└── static/
    ├── css/                 # bootstrap.min.css, site.css
    └── js/                  # react/axios/bootstrap/babel + 三個 React app
scripts/download_assets.py   # 下載離線前端資源
tests/                       # pytest:repository / service / controller
```

## 測試

```powershell
python -m pytest -q
```

爬蟲已透過 `monkeypatch` 模擬,測試完全離線執行。

## Playwright MCP 開發提示

開發時若使用 **Playwright MCP** 探索博客來頁面結構(例如新版型),可在 MCP 中操作搜尋頁,確認選擇器後再回到 [`book_search_service.py`](app/services/book_search_service.py) 同步調整 `_parse_item` 的 selector。執行階段仍由本機 `playwright` 套件直接驅動 Chromium。

## 安全注意

- 所有 SQL 透過 SQLAlchemy ORM,杜絕 SQL Injection。
- React 不使用 `dangerouslySetInnerHTML`;Jinja2 預設跳脫,避免 XSS。
- 對外請求 (`books.com.tw`) 屬唯讀爬蟲,僅讀取公開搜尋頁。
