from sqlalchemy import func
from extensions import db
from models.food_item import FoodItem
from models.analysis import Analysis


class FoodItemRepository:
    @staticmethod
    def bulk_create(analysis_id: int, items: list[dict]) -> list[FoodItem]:
        objs = []
        for it in items:
            objs.append(FoodItem(
                analysis_id=analysis_id,
                name=it.get("name") or "Unknown",
                category=it.get("category"),
                calories=float(it.get("calories") or 0),
                protein_g=_to_float(it.get("protein_g")),
                fat_g=_to_float(it.get("fat_g")),
                carbs_g=_to_float(it.get("carbs_g")),
                confidence=_to_float(it.get("confidence")),
            ))
        db.session.bulk_save_objects(objs)
        db.session.commit()
        return objs

    @staticmethod
    def category_distribution(user_id: int):
        rows = (
            db.session.query(
                FoodItem.category,
                func.count(FoodItem.id),
                func.coalesce(func.sum(FoodItem.calories), 0.0),
            )
            .join(Analysis, Analysis.id == FoodItem.analysis_id)
            .filter(Analysis.user_id == user_id)
            .group_by(FoodItem.category)
            .order_by(func.count(FoodItem.id).desc())
            .all()
        )
        return [
            {"category": (c or "Other"), "count": int(cnt), "calories": float(cal)}
            for c, cnt, cal in rows
        ]

    @staticmethod
    def top_food(user_id: int):
        row = (
            db.session.query(FoodItem.name, func.count(FoodItem.id).label("c"))
            .join(Analysis, Analysis.id == FoodItem.analysis_id)
            .filter(Analysis.user_id == user_id)
            .group_by(FoodItem.name)
            .order_by(func.count(FoodItem.id).desc())
            .first()
        )
        return row.name if row else None


def _to_float(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
