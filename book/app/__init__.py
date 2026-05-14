from flask import Flask

from app.config import Config
from app.extensions import db


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    db.init_app(app)

    # Import models so SQLAlchemy registers them
    from app.models import search_query, book_result  # noqa: F401

    # Register blueprints
    from app.controllers.mvc.home_controller import home_bp
    from app.controllers.mvc.history_controller import history_bp
    from app.controllers.mvc.dashboard_controller import dashboard_bp
    from app.controllers.api.book_api_controller import book_api_bp
    from app.controllers.api.search_record_api_controller import search_record_api_bp
    from app.controllers.api.stats_api_controller import stats_api_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(book_api_bp)
    app.register_blueprint(search_record_api_bp)
    app.register_blueprint(stats_api_bp)

    with app.app_context():
        db.create_all()
        _ensure_columns()

    return app


def _ensure_columns() -> None:
    """對既有 SQLite 資料庫進行最小遷移:補齊新版欄位。"""
    from sqlalchemy import text

    required = {
        "search_queries": [
            ("primary_category", "VARCHAR(50)"),
            ("summary_text", "TEXT"),
        ],
        "book_results": [
            ("category", "VARCHAR(50)"),
            ("description", "TEXT"),
            ("summary", "VARCHAR(500)"),
        ],
    }
    for table, columns in required.items():
        existing = {
            row[1]
            for row in db.session.execute(text(f"PRAGMA table_info({table})"))
        }
        for name, col_type in columns:
            if name not in existing:
                db.session.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN {name} {col_type}")
                )
        db.session.commit()
