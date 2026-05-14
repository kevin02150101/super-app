"""Flask 應用程式工廠。

依照 AGENTS 規範採用 Repository / Service / MVC Controller / Web API 四層分離,
每個功能模組(book、calendar、calories、summary、vibespec)均自成藍圖。
"""
from __future__ import annotations

from flask import Flask

from .config import Config
from .extensions import db


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    # 確保 instance 目錄存在(SQLite 檔存放處)
    import os
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    # --- 註冊 MVC Controller (View Page) ---
    from .controllers.home_controller import home_bp
    from .controllers.book_controller import book_bp
    from .controllers.calendar_controller import calendar_bp
    from .controllers.calories_controller import calories_bp
    from .controllers.summary_controller import summary_bp
    from .controllers.vibespec_controller import vibespec_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(book_bp, url_prefix="/book")
    app.register_blueprint(calendar_bp, url_prefix="/calendar")
    app.register_blueprint(calories_bp, url_prefix="/calories")
    app.register_blueprint(summary_bp, url_prefix="/summary")
    app.register_blueprint(vibespec_bp, url_prefix="/vibespec")

    # --- 註冊 Web API Controller ---
    from .api.book_api import book_api
    from .api.calendar_api import calendar_api
    from .api.calories_api import calories_api
    from .api.summary_api import summary_api
    from .api.vibespec_api import vibespec_api

    app.register_blueprint(book_api, url_prefix="/api/book")
    app.register_blueprint(calendar_api, url_prefix="/api/calendar")
    app.register_blueprint(calories_api, url_prefix="/api/calories")
    app.register_blueprint(summary_api, url_prefix="/api/summary")
    app.register_blueprint(vibespec_api, url_prefix="/api/vibespec")

    with app.app_context():
        # 確保所有 model 載入後建立資料表
        from .models import (  # noqa: F401
            book_record,
            calendar_event,
            calorie_record,
            summary_record,
            vibespec_record,
        )
        db.create_all()

        # Lightweight auto-migration for new columns added in dev
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        cols = {c["name"] for c in inspector.get_columns("summary_records")}
        if "chart_data" not in cols:
            with db.engine.begin() as conn:
                conn.execute(text("ALTER TABLE summary_records ADD COLUMN chart_data TEXT"))

    return app
