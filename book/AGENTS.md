# AGENTS.md

本文件為 AI Coding Agent 與開發者協作時的專案規範與架構指引。所有程式碼產出、重構與審查皆須遵守此文件之規定。

---

## 1. 專案總覽

- **後端語言/框架**：Python 3.x + Flask
- **前端技術堆疊**：原生 HTML5 + Meta React + Bootstrap 5.3 + Axios（皆採 **離線本地檔案**，**嚴禁** 使用任何 CDN）
- **設計風格**：Hero 風格首屏 + RWD 響應式
- **資料存取**：Repository Pattern
- **架構分層**：Repository → Service → Controller(MVC / Web API)

---

## 2. 後端系統架構（分層規範）

採嚴格四層分離，**禁止跨層呼叫**（例如 Controller 不得直接存取 Repository）。

```
┌─────────────────────────────────────────────────────┐
│  MVC Controller     │     Web API Controller        │ ← 表現層
│  (回傳 render_template) │ (回傳 jsonify / RESTful)  │
├─────────────────────────────────────────────────────┤
│                  Service Layer                      │ ← 商業邏輯
├─────────────────────────────────────────────────────┤
│                Repository Layer                     │ ← 資料存取
├─────────────────────────────────────────────────────┤
│              Model / ORM (SQLAlchemy)               │ ← 資料模型
└─────────────────────────────────────────────────────┘
```

### 2.1 建議目錄結構

```
project_root/
├── app/
│   ├── __init__.py              # Flask App Factory
│   ├── config.py                # 設定檔
│   ├── extensions.py            # db、migrate、login_manager 等
│   ├── models/                  # SQLAlchemy ORM 模型
│   │   └── user.py
│   ├── repositories/            # Repository 層（資料存取）
│   │   ├── base_repository.py
│   │   └── user_repository.py
│   ├── services/                # Service 層（商業邏輯）
│   │   └── user_service.py
│   ├── controllers/
│   │   ├── mvc/                 # MVC Controller（回傳 HTML 視圖）
│   │   │   └── home_controller.py
│   │   └── api/                 # Web API Controller（回傳 JSON）
│   │       └── user_api_controller.py
│   ├── schemas/                 # 序列化 / 驗證 (marshmallow / pydantic)
│   ├── templates/               # Jinja2 模板
│   │   ├── layout.html
│   │   └── home/index.html
│   └── static/                  # 靜態資源（離線）
│       ├── css/
│       │   └── bootstrap.min.css
│       ├── js/
│       │   ├── react.production.min.js
│       │   ├── react-dom.production.min.js
│       │   ├── babel.min.js
│       │   ├── axios.min.js
│       │   └── bootstrap.bundle.min.js
│       ├── webfonts/
│       └── img/
├── tests/
├── requirements.txt
├── run.py
└── AGENTS.md
```

### 2.2 Repository 層

- 唯一可直接操作 ORM/DB 的層級。
- 提供 CRUD 原語，**不含商業邏輯**。
- 每個 Aggregate / Entity 對應一個 Repository。
- 命名：`XxxRepository`，方法以資料動作為主：`find_by_id`, `find_all`, `add`, `update`, `delete`。

```python
# app/repositories/user_repository.py
from app.extensions import db
from app.models.user import User

class UserRepository:
    def find_by_id(self, user_id: int) -> User | None:
        return db.session.get(User, user_id)

    def find_by_email(self, email: str) -> User | None:
        return User.query.filter_by(email=email).first()

    def add(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user
```

### 2.3 Service 層

- 封裝商業邏輯、交易邊界、驗證、跨 Repository 協調。
- **僅** 呼叫 Repository，不直接觸碰 `db.session`（交易封裝除外）。
- 拋出領域例外（Domain Exception），由 Controller 統一轉譯為 HTTP 回應。

```python
# app/services/user_service.py
from app.repositories.user_repository import UserRepository
from app.models.user import User

class UserService:
    def __init__(self, user_repo: UserRepository | None = None):
        self.user_repo = user_repo or UserRepository()

    def register(self, email: str, password: str) -> User:
        if self.user_repo.find_by_email(email):
            raise ValueError("Email 已被註冊")
        user = User(email=email)
        user.set_password(password)
        return self.user_repo.add(user)
```

### 2.4 MVC Controller

- 路徑前綴：通常掛載在根目錄或 `/`。
- 回傳 `render_template(...)`，將 ViewModel 傳給 Jinja2。
- **不得** 回傳 JSON。
- 使用 `Blueprint` 註冊。

```python
# app/controllers/mvc/home_controller.py
from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__, url_prefix="/")

@home_bp.get("/")
def index():
    return render_template("home/index.html", title="首頁")
```

### 2.5 Web API Controller

- 路徑前綴：`/api/v{n}/...`，採 RESTful 命名。
- 回傳 `jsonify(...)`，統一回應格式：

```json
{ "success": true, "data": {}, "message": "" }
```

- 錯誤處理透過 `@blueprint.errorhandler` 或全域 `app.errorhandler`。
- **不得** 回傳 HTML。

```python
# app/controllers/api/user_api_controller.py
from flask import Blueprint, request, jsonify
from app.services.user_service import UserService

user_api_bp = Blueprint("user_api", __name__, url_prefix="/api/v1/users")
service = UserService()

@user_api_bp.post("")
def create_user():
    payload = request.get_json() or {}
    user = service.register(payload["email"], payload["password"])
    return jsonify({"success": True, "data": {"id": user.id, "email": user.email}}), 201
```

### 2.6 分層呼叫規則（強制）

| 來源 \ 目標     | Repository | Service | Controller |
| --------------- | :--------: | :-----: | :--------: |
| MVC Controller  |     ❌      |    ✅    |     —      |
| API Controller  |     ❌      |    ✅    |     —      |
| Service         |     ✅      |    ✅    |     ❌      |
| Repository      |     —      |    ❌    |     ❌      |

---

## 3. 前端技術堆疊規範

### 3.1 離線架構（強制）

- **嚴禁** 使用任何 CDN（包含 `cdn.jsdelivr.net`, `unpkg.com`, `cdnjs.cloudflare.com`, `bootstrapcdn.com` 等）。
- 所有第三方資源必須下載至 `app/static/` 並由 Flask 透過 `url_for('static', filename=...)` 提供。
- `<link>` / `<script>` 之 `href` / `src` 一律指向本機 `static/` 路徑。
- 字型（Bootstrap Icons / Google Fonts）需下載至 `static/webfonts/` 並以本機 `@font-face` 引入。

### 3.2 必備離線資源清單

| 套件                | 版本   | 放置路徑                               |
| ------------------- | ------ | -------------------------------------- |
| Bootstrap CSS       | 5.3.x  | `static/css/bootstrap.min.css`         |
| Bootstrap JS Bundle | 5.3.x  | `static/js/bootstrap.bundle.min.js`    |
| React (production)  | 18.x   | `static/js/react.production.min.js`    |
| ReactDOM            | 18.x   | `static/js/react-dom.production.min.js`|
| Babel Standalone    | 7.x    | `static/js/babel.min.js`（僅 dev）     |
| Axios               | 1.x    | `static/js/axios.min.js`               |

> Production 應預先以建置工具編譯 JSX，避免在瀏覽器使用 Babel Standalone。

### 3.3 Meta React 整合方式

- 採用 **Meta React（純 React，不使用 Next.js）** 嵌入 Flask 模板。
- 每個頁面以 `<div id="root-xxx"></div>` 為掛載點，由獨立的 React Bundle 渲染。
- 與 Flask 的整合採「島嶼架構（Islands）」：頁面骨架由 Jinja2 渲染，互動區塊交給 React。

```html
<!-- app/templates/layout.html -->
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
  <title>{{ title }}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/bootstrap.min.css') }}" />
  <link rel="stylesheet" href="{{ url_for('static', filename='css/site.css') }}" />
</head>
<body>
  {% block content %}{% endblock %}

  <script src="{{ url_for('static', filename='js/bootstrap.bundle.min.js') }}"></script>
  <script src="{{ url_for('static', filename='js/axios.min.js') }}"></script>
  <script src="{{ url_for('static', filename='js/react.production.min.js') }}"></script>
  <script src="{{ url_for('static', filename='js/react-dom.production.min.js') }}"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

### 3.4 Axios 非同步呼叫規範

- 所有前端 → 後端的 HTTP 通訊統一以 `axios` 處理，**禁止** 使用 `fetch` 或 `XMLHttpRequest` 直呼。
- 建立全域 instance，集中設定 `baseURL`、攔截器、CSRF Token。

```js
// app/static/js/api-client.js
const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 10000,
  headers: { "Content-Type": "application/json" }
});

apiClient.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    console.error("[API ERROR]", err);
    return Promise.reject(err);
  }
);
```

### 3.5 RWD 響應式規範

- 一律以 Bootstrap 5.3 Grid（`container`, `row`, `col-*`）建構版面。
- 斷點對應：`sm ≥576`, `md ≥768`, `lg ≥992`, `xl ≥1200`, `xxl ≥1400`。
- 圖片使用 `img-fluid`；表格使用 `table-responsive`。
- **禁止** 寫死 `px` 寬度於佈局；改用 `rem` / `%` / `vw`。
- 行動裝置優先（Mobile First）：先寫小螢幕樣式，再以 `@media (min-width)` 加大。

### 3.6 Hero 風格規範

每個主要頁面首屏應包含 **Hero Section**：

- 全寬區塊（`container-fluid`），背景為高解析圖、漸層或純色。
- 包含：大標題（`display-3`/`display-4`）、副標、CTA 按鈕（`btn btn-primary btn-lg`）。
- 高度建議 `min-height: 70vh`（桌機）/ `min-height: 50vh`（手機）。
- 文字需具足夠對比度（WCAG AA），背景圖加遮罩（`rgba(0,0,0,.4)`）。

```html
<section class="hero d-flex align-items-center text-white"
         style="min-height:70vh; background:
                linear-gradient(rgba(0,0,0,.5), rgba(0,0,0,.5)),
                url('{{ url_for('static', filename='img/hero.jpg') }}') center/cover no-repeat;">
  <div class="container text-center">
    <h1 class="display-3 fw-bold">標題訴求</h1>
    <p class="lead mb-4">一句話說明產品價值</p>
    <a href="#cta" class="btn btn-primary btn-lg px-5">立即開始</a>
  </div>
</section>
```

---

## 4. 程式碼規範

### 4.1 Python

- 遵循 **PEP 8**；行寬 100。
- 使用 **Type Hints**（Python 3.10+ 原生語法 `list[int]`, `X | None`）。
- 格式化工具：`black`；Lint：`ruff` 或 `flake8`；Import 排序：`isort`。
- 例外處理：Service 拋領域例外，Controller 轉譯為 HTTP 狀態碼。
- 命名：類別 `PascalCase`、函式/變數 `snake_case`、常數 `UPPER_SNAKE_CASE`。

### 4.2 JavaScript / React

- ES2020+；統一以 `const` / `let`，**禁用** `var`。
- React 元件：函式式 + Hooks，**不使用** Class Component。
- 元件命名 `PascalCase`，檔名與元件同名。
- JSX 屬性順序：`key` → `ref` → `id`/`className` → 一般 props → 事件 → `style`。

### 4.3 命名與路由

- API 路由：複數名詞，kebab-case，`/api/v1/user-profiles`。
- MVC 路由：語意化，`/products`、`/products/<id>`。
- Blueprint 名稱與檔名一致。

---

## 5. 安全規範（OWASP Top 10）

- **SQL Injection**：一律透過 ORM/參數化查詢；禁用字串拼接 SQL。
- **XSS**：Jinja2 預設自動跳脫；React 不使用 `dangerouslySetInnerHTML`。
- **CSRF**：表單與非 GET API 啟用 CSRF Token（`flask-wtf` / 自訂 header）。
- **驗證授權**：使用 `flask-login` 或 JWT；於 Service 層檢查授權。
- **密碼**：以 `werkzeug.security.generate_password_hash`（bcrypt/scrypt）儲存。
- **輸入驗證**：於 Schema 層（marshmallow / pydantic）做白名單驗證。
- **機密資訊**：經由環境變數注入；**禁止** commit 至版本庫。

---

## 6. 測試規範

- 框架：`pytest` + `pytest-flask`。
- 覆蓋率目標：Service ≥ 80%、Repository ≥ 70%。
- 分層測試：
  - Repository：以 in-memory SQLite 測試。
  - Service：以 Mock Repository 測試商業邏輯。
  - Controller：以 `app.test_client()` 做整合測試。
- 測試檔命名：`tests/test_<module>.py`；測試函式 `test_<行為>_<預期>`。

---

## 7. AI Agent 操作守則

當 AI Agent 在本專案中產出/修改程式碼時，**必須**：

1. **遵守分層**：新增資料存取邏輯放 Repository、商業邏輯放 Service、HTTP 處理放 Controller。
2. **區分 MVC 與 API**：根據需求明確選擇模板回應或 JSON 回應，**不得混用**。
3. **離線資源檢查**：產出 HTML 時，**禁止** 出現任何 `http(s)://...cdn...` 連結，所有資源以 `url_for('static', ...)` 引用。
4. **使用 Axios**：前端非同步請求一律 `axios`，並透過共用 `apiClient`。
5. **RWD 與 Hero**：頁面樣板須含 Hero Section，並以 Bootstrap 5.3 Grid 實作 RWD。
6. **附帶測試**：新增 Service / Repository 時需同步補對應 `pytest` 測試。
7. **不過度工程**：僅實作明確需求，不擅自加入未要求之框架或抽象。
8. **編輯前先讀檔**：修改既有檔案前，先讀取現有內容以理解上下文。

---

## 8. 啟動指令

```powershell
# 建立虛擬環境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
$env:FLASK_APP = "run.py"
$env:FLASK_ENV = "development"

# 啟動
flask run --host=0.0.0.0 --port=5000
```

---

> 本文件為專案最高層級規範。任何違反條款（特別是分層規則與離線資源規則）的程式碼，皆視為不合規，須立即修正。
