from extensions import db


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

    def to_dict(self):
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
