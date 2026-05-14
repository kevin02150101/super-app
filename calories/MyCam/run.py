"""MyCam 啟動入口。

用法：
    python run.py                  # 預設 0.0.0.0:5000，debug 由 FLASK_ENV 決定
    HOST=127.0.0.1 PORT=8000 python run.py
    或於 .env 設定 HOST / PORT / FLASK_ENV
"""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    # macOS 的 AirPlay Receiver 預設佔用 5000，因此採 5001
    port = int(os.environ.get("PORT", "5001"))
    debug = os.environ.get("FLASK_ENV", "development").lower() != "production"
    app.run(host=host, port=port, debug=debug)
