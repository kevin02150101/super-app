# 17 — 部署與啟動說明

## 1. 本機開發

```bash
git clone <repo> MyCam && cd MyCam
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env 填入 GEMINI_API_KEY
flask --app app.py --debug run -p 5000
# 瀏覽 http://127.0.0.1:5000
```

第一次啟動會自動建立 `instance/mycam.db`。

## 2. 生產（單機 / 內網）

使用 `gunicorn`：

```bash
pip install gunicorn
gunicorn -w 3 -b 0.0.0.0:8000 "app:create_app()"
```

建議搭配 Nginx 反向代理 + HTTPS。

### Nginx 範例

```
server {
  listen 80;
  server_name mycam.local;
  client_max_body_size 10m;

  location /static/ {
    alias /opt/MyCam/static/;
    expires 7d;
  }

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

## 3. Docker（可選）

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_ENV=production
EXPOSE 8000
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "app:create_app()"]
```

`docker run`：
```bash
docker build -t mycam .
docker run -d -p 8000:8000 \
  -e GEMINI_API_KEY=xxx \
  -e SECRET_KEY=yyy \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/static/uploads:/app/static/uploads \
  --name mycam mycam
```

## 4. 環境變數總表

| 變數 | 必填 | 預設 | 說明 |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Flask Session 加密 |
| `GEMINI_API_KEY` | ✅ | — | Google Gemini API Key |
| `GEMINI_MODEL` |  | `gemini-2.5-flash` | 模型名稱 |
| `DATABASE_URL` |  | `sqlite:///instance/mycam.db` | DB URL |
| `MAX_UPLOAD_MB` |  | `8` | 上傳上限 |
| `FLASK_ENV` |  | `production` | 環境 |

## 5. 安全注意

- 強制 HTTPS（Set-Cookie `Secure`、`HttpOnly`、`SameSite=Lax`）。
- 上傳目錄禁止執行（Nginx `location ~ \.(php|py)$ { deny all; }`）。
- 啟用 Flask-Limiter 防止濫用 `/api/analyze`。
- 密碼以 `werkzeug.security.generate_password_hash`（PBKDF2 / scrypt）儲存。
- 切勿提交 `.env` 或 `instance/*.db` 至版本控制。

## 6. 備份

- 定期備份 `instance/mycam.db` 與 `static/uploads/`。
- 建議每日 cron：`sqlite3 mycam.db ".backup '/backup/mycam-$(date +%F).db'"`。
