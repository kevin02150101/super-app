# 03 — MVC 層設計

## 1. 職責

- 接收 HTTP 請求，渲染 Jinja2 模板。
- 處理 Session / Flash Message。
- **不得**直接操作 DB、不得直接呼叫 Gemini。

## 2. Blueprint 範例

```python
# controllers/dashboard_controller.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.stats_service import StatsService

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@bp.get("/")
@login_required
def index():
    kpi = StatsService.kpi_summary(current_user.id)
    return render_template("dashboard/index.html", kpi=kpi)
```

## 3. Controller 對應路由

| Controller | 路由 | View |
|---|---|---|
| `home_controller` | `/` | `home/index.html` |
| `auth_controller` | `/auth/login`, `/auth/register`, `/auth/logout` | `auth/*.html` |
| `dashboard_controller` | `/dashboard` | `dashboard/index.html` |
| `capture_controller` | `/capture` | `capture/index.html` |
| `history_controller` | `/history`, `/history/<id>` | `history/*.html` |
| `stats_controller` | `/stats` | `stats/index.html` |

## 4. View 規範

- 一律繼承 `templates/base.html`。
- 需登入頁面套用 `_layout/sidebar.html`。
- Vue 3 元件以 `<script type="module">` 於頁面尾端掛載，元素以 `id="app"` 包覆。

## 5. 錯誤處理

- 401 → 重導向 `/auth/login`。
- 403 → 顯示 `errors/403.html`。
- 500 → 顯示 `errors/500.html`。
