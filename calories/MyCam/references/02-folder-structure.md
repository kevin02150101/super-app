# 02 — 完整資料夾與檔案結構

```
MyCam/
├── app.py                          # Flask Application Factory + 註冊 Blueprint
├── config.py                       # 設定（讀取 .env）
├── .env.example                    # 環境變數範本（GEMINI_API_KEY 等）
├── requirements.txt
├── README.md
│
├── controllers/                    # MVC — Controller（Blueprint，回傳 HTML）
│   ├── __init__.py
│   ├── home_controller.py          # /
│   ├── auth_controller.py          # /auth/*
│   ├── dashboard_controller.py     # /dashboard
│   ├── capture_controller.py       # /capture
│   ├── history_controller.py       # /history, /history/<id>
│   └── stats_controller.py         # /stats
│
├── api/                            # Web API — 回傳 JSON
│   ├── __init__.py
│   ├── auth_api.py                 # /api/auth/*
│   ├── analyze_api.py              # /api/analyze
│   ├── analysis_api.py             # /api/analyses, /api/analyses/<id>
│   └── stats_api.py                # /api/stats/*
│
├── services/                       # Service 層 — 業務邏輯
│   ├── __init__.py
│   ├── auth_service.py
│   ├── analysis_service.py
│   ├── ai_service.py               # **唯一**封裝 Gemini API 呼叫
│   ├── image_service.py            # Pillow 影像處理
│   └── stats_service.py
│
├── repositories/                   # Repository 層
│   ├── __init__.py
│   ├── base_repository.py
│   ├── user_repository.py
│   ├── analysis_repository.py
│   └── food_item_repository.py
│
├── models/                         # SQLAlchemy Models
│   ├── __init__.py
│   ├── user.py
│   ├── analysis.py
│   └── food_item.py
│
├── schemas/                        # DTO / Pydantic / Marshmallow（可選）
│   ├── auth_schema.py
│   ├── analysis_schema.py
│   └── stats_schema.py
│
├── templates/                      # Jinja2
│   ├── base.html
│   ├── _layout/
│   │   ├── navbar.html
│   │   ├── sidebar.html
│   │   └── hero.html
│   ├── home/index.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/index.html
│   ├── capture/index.html
│   ├── history/
│   │   ├── list.html
│   │   └── detail.html
│   └── stats/index.html
│
├── static/
│   ├── css/
│   │   ├── hero-dashboard.css      # Hero Dashboard 主題
│   │   └── components.css
│   ├── js/
│   │   ├── app.js                  # 全域 Vue 設定
│   │   ├── components/
│   │   │   ├── CaptureUploader.js
│   │   │   ├── AnalysisCard.js
│   │   │   ├── HistoryTable.js
│   │   │   └── KpiCard.js
│   │   └── pages/
│   │       ├── dashboard.js
│   │       ├── capture.js
│   │       └── stats.js
│   ├── vendor/                     # 地端 vendor（**禁止 CDN**）
│   │   ├── bootstrap-5.3/
│   │   ├── vue-3.0/
│   │   ├── axios/
│   │   ├── sweetalert2/
│   │   └── chartjs/
│   └── uploads/                    # 使用者上傳影像（依 user_id 分目錄）
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_analysis.py
│   ├── test_ai_service.py          # 以 mock 取代 Gemini
│   └── test_api.py
│
├── instance/
│   └── mycam.db                    # SQLite（執行時建立）
│
└── migrations/                     # 若採用 Flask-Migrate（可選）
```
