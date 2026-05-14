# 07 — SQLite 資料表設計

## 1. ERD

```
users (1) ────< analyses (1) ────< food_items
```

## 2. DDL

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    nickname      TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analyses (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL,
    image_path       TEXT NOT NULL,
    total_calories   REAL NOT NULL DEFAULT 0,
    summary          TEXT,
    health_advice    TEXT,
    raw_json         TEXT,                       -- Gemini 原始 JSON
    analyzed_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_analyses_user_time ON analyses(user_id, analyzed_at DESC);

CREATE TABLE food_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id   INTEGER NOT NULL,
    name          TEXT NOT NULL,
    category      TEXT,                          -- 主食/蛋白質/蔬菜/水果/飲料/甜點...
    calories      REAL NOT NULL DEFAULT 0,
    protein_g     REAL,
    fat_g         REAL,
    carbs_g       REAL,
    confidence    REAL,                          -- 0~1
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);
CREATE INDEX idx_food_items_category ON food_items(category);
```

## 3. SQLAlchemy Model 範例

```python
# models/analysis.py
from datetime import datetime
from extensions import db

class Analysis(db.Model):
    __tablename__ = "analyses"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_path = db.Column(db.String, nullable=False)
    total_calories = db.Column(db.Float, default=0)
    summary = db.Column(db.Text)
    health_advice = db.Column(db.Text)
    raw_json = db.Column(db.Text)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("FoodItem", backref="analysis", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "image_path": self.image_path,
            "total_calories": self.total_calories,
            "summary": self.summary,
            "health_advice": self.health_advice,
            "analyzed_at": self.analyzed_at.isoformat(),
            "items": [i.to_dict() for i in self.items],
        }
```
