# 06 — Web API 層設計

## 1. 職責

- 對前端 Vue 3 提供 JSON API。
- 驗證 Session（Flask-Login `@login_required`）。
- 解析 / 驗證輸入（schemas/）。
- 呼叫 Service 並序列化回應。

## 2. 回應格式（統一）

成功：
```json
{ "ok": true, "data": { ... } }
```

錯誤：
```json
{ "ok": false, "error": { "code": "STR", "message": "..." } }
```

## 3. Blueprint 範例

```python
# api/analyze_api.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from services.analysis_service import AnalysisService

bp = Blueprint("analyze_api", __name__, url_prefix="/api")

@bp.post("/analyze")
@login_required
def analyze():
    file = request.files.get("image")
    if not file:
        return jsonify(ok=False, error={"code": "NO_FILE", "message": "缺少影像"}), 400
    analysis = AnalysisService.analyze(current_user.id, file)
    return jsonify(ok=True, data=analysis.to_dict()), 201
```

## 4. CSRF / CORS

- 因前端為地端同源，**啟用** Flask CSRF（對非 GET 的 form/api 套用）。
- API 從 cookie 取 CSRF token，前端 axios 預設帶上 `X-CSRFToken` header。

## 5. 速率限制（建議）

- `/api/analyze` 套 Flask-Limiter：每分鐘 5 次。
