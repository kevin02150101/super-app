# MyCam — AI 食物影像分析平台

以 Python Flask 為核心、Google Gemini 為 AI 引擎的飲食分析網站。
登入後可拍照或上傳相片，自動辨識食物、估算卡路里、產生 Hero Dashboard 儀表板與個人歷史紀錄。

> **架構**：MVC + Repository + Service + Web API（四層分離）
> **前端**：Bootstrap 5.3 + Vue 3 + axios + SweetAlert2 + Chart.js
> **AI**：僅使用 Google Gemini API（**禁止** Ollama / 地端 `gemma4:e2b` 等地端模型）

---

## 1. 快速開始

### (a) 安裝

```bash
cd MyCam
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### (b) 設定環境變數

```bash
cp .env.example .env
# 編輯 .env，將 GEMINI_API_KEY 填入你自己於 Google AI Studio 取得的 API Key
# https://aistudio.google.com/apikey
```

> ⚠️ **絕對不要**把 `.env` 或 API Key 提交到版控。已預先加入 `.gitignore`。

### (c) 啟動

```bash
python app.py
# 或
flask --app app.py --debug run -p 5000
```

開啟瀏覽器：<http://127.0.0.1:5000>

第一次啟動會自動建立 SQLite（位於 `instance/mycam.db` 或 `mycam.db`）。

---

## 2. 專案結構

```
MyCam/
├── app.py                  # Flask Application Factory
├── config.py               # 設定（讀 .env）
├── extensions.py           # SQLAlchemy / Login / CSRF / Limiter
├── errors.py               # MyCamError
│
├── controllers/            # MVC 層（HTML）
├── api/                    # Web API 層（JSON）
├── services/               # Service 層
│   └── ai_service.py       # 唯一封裝 Gemini
├── repositories/           # Repository 層
├── models/                 # SQLAlchemy Models
│
├── templates/              # Jinja2
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/            # 使用者影像
│
├── tests/                  # pytest
├── SKILL.md                # Agent Skills 核心規格
└── references/             # 分層細節規格
```

---

## 3. 功能

- ✅ 使用者註冊 / 登入 / 登出（Flask-Login）
- ✅ 拍照（getUserMedia）或拖曳上傳影像
- ✅ Google Gemini AI 食物辨識（強制 JSON Schema 輸出）
- ✅ Dashboard：今日卡路里 / 歷史筆數 / 常見食物 / 30 日趨勢 / 種類分佈
- ✅ 歷史列表 / 單筆詳情 / 刪除
- ✅ 統計頁（60 日趨勢 + 分類佔比）
- ✅ SweetAlert2 全域提示
- ✅ Flask-Limiter 對 `/api/analyze` 限流 10/分

---

## 4. API 速覽

詳見 [references/11-api-endpoints.md](references/11-api-endpoints.md)。

| Method | Path | 說明 |
|---|---|---|
| POST | `/api/auth/register` / `/login` / `/logout` | 認證 |
| POST | `/api/analyze` (multipart `image`) | 拍照/上傳分析 |
| GET  | `/api/analyses?page=&per_page=` | 歷史列表 |
| GET  | `/api/analyses/<id>` | 單筆詳情 |
| DELETE | `/api/analyses/<id>` | 刪除 |
| GET  | `/api/stats/summary` / `/calories` / `/categories` | 統計 |

回應統一格式：`{ ok, data }` 或 `{ ok: false, error: { code, message } }`。

---

## 5. 測試

```bash
pytest -q
```

`tests/` 已內建：
- 註冊 / 登入
- `/api/analyze` 未登入 401
- 以 mock 取代 Gemini，驗證完整分析 → 入庫流程

---

## 6. 部署

詳見 [references/17-deployment.md](references/17-deployment.md)。

最小化生產啟動：

```bash
pip install gunicorn
gunicorn -w 3 -b 0.0.0.0:8000 "app:create_app()"
```

---

## 7. AI 模組規範（重要）

`services/ai_service.py` 是**唯一**呼叫 Gemini 的位置：

- 必須透過 `os.environ["GEMINI_API_KEY"]`（由 `.env` 載入）。
- 模型預設 `gemini-2.5-flash`（可改 `.env` 的 `GEMINI_MODEL`）。
- 強制 `response_mime_type = "application/json"` + `response_schema`，避免不可控輸出。
- 禁止 `import ollama`、禁止任何地端推論模型。

---

## 8. 鏡頭啟動需求

- 瀏覽器要求 **HTTPS** 或 `localhost` 才能呼叫 `getUserMedia`。
- 行動裝置請確認允許頁面使用相機權限。

---

## 9. License

MIT
