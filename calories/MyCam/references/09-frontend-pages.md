# 09 — 前端頁面規劃

## 1. 頁面清單

| 頁面 | 路徑 | 主要區塊 |
|---|---|---|
| Landing | `/` | Hero、特色卡片、CTA |
| 註冊 | `/auth/register` | Form（email / 暱稱 / 密碼） |
| 登入 | `/auth/login` | Form（email / 密碼） |
| Dashboard | `/dashboard` | Hero KPI、最近分析、卡路里曲線、種類圓餅 |
| 拍照/上傳 | `/capture` | 鏡頭預覽、拍照按鈕、檔案上傳、即時結果卡 |
| 歷史列表 | `/history` | 篩選列、表格 / 卡片清單、分頁 |
| 歷史詳情 | `/history/<id>` | 影像、食物明細卡片、營養素表 |
| 統計 | `/stats` | 卡路里趨勢、種類分佈、Top 食物 |

## 2. 共用版型

- 頂部：Navbar（Logo `MyCam`、使用者頭像下拉）。
- 左側：Sidebar（Dashboard / 拍照分析 / 歷史 / 統計 / 登出）。
- 內容：Hero 區（漸層背景 + 標題 + Sub-title + 行動按鈕）+ 內容卡片。

## 3. 互動細節

- 所有 API 呼叫使用 axios + `withCredentials: true`。
- 所有提示使用 SweetAlert2（成功 / 警告 / 錯誤）。
- 表單以 Vue 3 `reactive` 管理；前端做基本驗證，伺服器最終驗證。
- 鏡頭使用 `navigator.mediaDevices.getUserMedia({ video: true })`，拍照轉成 `Blob` 上傳。
