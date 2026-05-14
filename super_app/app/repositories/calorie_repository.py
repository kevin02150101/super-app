"""卡路里 Repository(移植自 MyCam)。"""
from __future__ import annotations

from ..extensions import db
from ..models.calorie_record import Analysis, FoodItem


class AnalysisRepository:
    @staticmethod
    def create(
        image_path: str,
        total_calories: float,
        summary: str,
        health_advice: str,
        raw_json: str,
    ) -> Analysis:
        a = Analysis(
            image_path=image_path,
            total_calories=total_calories,
            summary=summary,
            health_advice=health_advice,
            raw_json=raw_json,
        )
        db.session.add(a)
        db.session.commit()
        return a

    @staticmethod
    def get(analysis_id: int) -> Analysis | None:
        return db.session.get(Analysis, analysis_id)

    @staticmethod
    def list_recent(limit: int = 30) -> list[Analysis]:
        return Analysis.query.order_by(Analysis.analyzed_at.desc()).limit(limit).all()

    @staticmethod
    def delete(analysis_id: int) -> bool:
        a = AnalysisRepository.get(analysis_id)
        if not a:
            return False
        db.session.delete(a)
        db.session.commit()
        return True


class FoodItemRepository:
    @staticmethod
    def bulk_create(analysis_id: int, items: list[dict]) -> list[FoodItem]:
        created: list[FoodItem] = []
        for it in items:
            fi = FoodItem(
                analysis_id=analysis_id,
                name=str(it.get("name", "未知")),
                category=str(it.get("category", "其他")),
                calories=float(it.get("calories") or 0),
                protein_g=it.get("protein_g"),
                fat_g=it.get("fat_g"),
                carbs_g=it.get("carbs_g"),
                confidence=it.get("confidence"),
            )
            db.session.add(fi)
            created.append(fi)
        db.session.commit()
        return created
