# 15 — 開發步驟

## 階段 0：環境準備
1. 安裝 Python 3.11+。
2. 建虛擬環境：`python -m venv .venv && source .venv/bin/activate`。
3. 申請 Gemini API Key（Google AI Studio）。
4. 複製 `.env.example` 為 `.env`，填入 `GEMINI_API_KEY`。

## 階段 1：骨架
1. 建立資料夾結構（見 `02-folder-structure.md`）。
2. `requirements.txt` 加入：
   ```
   Flask>=3.0
   Flask-Login>=0.6
   Flask-SQLAlchemy>=3.1
   Flask-WTF>=1.2
   Flask-Limiter>=3.5
   SQLAlchemy>=2.0
   Pillow>=10.0
   google-generativeai>=0.8
   python-dotenv>=1.0
   pytest>=8.0
   ```
3. 撰寫 `app.py` Application Factory；註冊所有 Blueprint。
4. 初始化 SQLite（`db.create_all()` 於首次啟動）。

## 階段 2：認證
1. 完成 `User` Model、`UserRepository`、`AuthService`。
2. 完成 `auth_controller`（頁面）+ `auth_api`（JSON）。
3. 寫 `tests/test_auth.py`。

## 階段 3：影像 + AI
1. 下載地端 vendor（bootstrap、vue、axios、sweetalert2、chartjs）至 `static/vendor/`。
2. `ImageService`（驗證、Resize、JPEG）。
3. `AIService.analyze_food`（依 `08-gemini-integration.md`）。
4. `AnalysisService.analyze` 流程串接；寫入 DB。
5. `/capture` 頁面 + `CaptureUploader` 元件。

## 階段 4：Dashboard / 歷史 / 統計
1. `StatsService`：KPI、時序、分類。
2. `dashboard_controller` + Chart.js 兩張圖。
3. `history_controller`：列表 / 詳情。
4. `stats_controller`：更完整統計頁。

## 階段 5：打磨
1. SweetAlert2 全域提示。
2. 速率限制、CSRF、檔案大小限制。
3. Logging + Error Page。
4. README、部署文件。
