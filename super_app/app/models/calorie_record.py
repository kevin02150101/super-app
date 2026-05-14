"""卡路里分析 Model(移植自 MyCam)。"""
from __future__ import annotations

from datetime import datetime

from ..extensions import db


class Analysis(db.Model):
    __tablename__ = "analyses"

    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(500), nullable=False)
    total_calories = db.Column(db.Float, nullable=False, default=0)
    summary = db.Column(db.Text)
    health_advice = db.Column(db.Text)
    raw_json = db.Column(db.Text)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    items = db.relationship(
        "FoodItem", backref="analysis", cascade="all, delete-orphan", lazy="joined"
    )

    def main_food(self):
        if not self.items:
            return None
        return max(self.items, key=lambda i: i.calories or 0).name

    def to_dict(self, include_items: bool = True) -> dict:
        d = {
            "id": self.id,
            "image_path": self.image_path,
            "total_calories": self.total_calories,
            "summary": self.summary,
            "health_advice": self.health_advice,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "main_food": self.main_food(),
        }
        if include_items:
            d["items"] = [i.to_dict() for i in self.items]
        return d


class FoodItem(db.Model):
    __tablename__ = "food_items"

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(
        db.Integer,
        db.ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), index=True)
    calories = db.Column(db.Float, nullable=False, default=0)
    protein_g = db.Column(db.Float)
    fat_g = db.Column(db.Float)
    carbs_g = db.Column(db.Float)
    confidence = db.Column(db.Float)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "calories": self.calories,
            "protein_g": self.protein_g,
            "fat_g": self.fat_g,
            "carbs_g": self.carbs_g,
            "confidence": self.confidence,
        }
