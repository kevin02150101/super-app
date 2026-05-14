# 05 — Service 層設計

## 1. 職責

- 封裝業務邏輯（驗證、流程編排、權限檢查、計算）。
- 整合多個 Repository 與外部服務（Gemini）。
- 對 Controller / API 提供以「使用者意圖」為單位的方法。

## 2. 模組清單

### AuthService
- `register(email, password, nickname) -> User`
- `login(email, password) -> User`
- `logout()`

### ImageService
- `validate(file_storage) -> None`（MIME、大小）
- `save(user_id, file_storage) -> str`（回傳路徑）
- `preprocess(path) -> bytes`（Resize ≤ 1024px、JPEG 壓縮）

### AIService（**唯一**呼叫 Gemini）
- `analyze_food(image_bytes, mime: str) -> dict`
- 內部：
  - 載入 `GEMINI_API_KEY`。
  - 構造 Prompt + JSON Schema（response_mime_type=application/json）。
  - 呼叫 `gemini-2.5-flash`。
  - 回傳結構化 dict（見 `08-gemini-integration.md`）。

### AnalysisService
- `analyze(user_id, file_storage) -> Analysis`
  1. `ImageService.validate / save / preprocess`
  2. `AIService.analyze_food`
  3. 寫入 `AnalysisRepository` + `FoodItemRepository`
  4. 回傳 Analysis（含食物明細）
- `list(user_id, page) -> Pagination`
- `get(user_id, id_) -> Analysis`
- `delete(user_id, id_) -> bool`

### StatsService
- `kpi_summary(user_id) -> dict`（今日卡路里、總筆數、最常食物）
- `calories_timeseries(user_id, days=30) -> list[{date, calories}]`
- `category_distribution(user_id) -> list[{category, count, calories}]`

## 3. 例外規約

- 業務錯誤丟出 `MyCamError(code, message, http_status)`。
- API 層統一以 errorhandler 轉成 JSON：
  ```json
  { "ok": false, "error": { "code": "AI_FAIL", "message": "..." } }
  ```
