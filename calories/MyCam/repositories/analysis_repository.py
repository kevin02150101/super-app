from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func

from extensions import db
from models.analysis import Analysis
from models.food_item import FoodItem


class AnalysisRepository:
    @staticmethod
    def create(user_id: int, image_path: str, total_calories: float,
               summary: str, health_advice: str, raw_json: str) -> Analysis:
        a = Analysis(
            user_id=user_id,
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
    def get_for_user(analysis_id: int, user_id: int) -> Optional[Analysis]:
        return (
            db.session.query(Analysis)
            .filter_by(id=analysis_id, user_id=user_id)
            .first()
        )

    @staticmethod
    def paginate(user_id: int, page: int = 1, per_page: int = 20):
        q = (
            db.session.query(Analysis)
            .filter_by(user_id=user_id)
            .order_by(Analysis.analyzed_at.desc())
        )
        return q.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def delete_for_user(analysis_id: int, user_id: int) -> bool:
        a = AnalysisRepository.get_for_user(analysis_id, user_id)
        if not a:
            return False
        db.session.delete(a)
        db.session.commit()
        return True

    @staticmethod
    def count(user_id: int) -> int:
        return db.session.query(Analysis).filter_by(user_id=user_id).count()

    @staticmethod
    def sum_calories_today(user_id: int) -> float:
        today = datetime.utcnow().date()
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)
        v = (
            db.session.query(func.coalesce(func.sum(Analysis.total_calories), 0.0))
            .filter(Analysis.user_id == user_id,
                    Analysis.analyzed_at >= start,
                    Analysis.analyzed_at < end)
            .scalar()
        )
        return float(v or 0)

    @staticmethod
    def daily_calories(user_id: int, days: int = 30):
        start = datetime.utcnow() - timedelta(days=days - 1)
        start = datetime(start.year, start.month, start.day)
        rows = (
            db.session.query(
                func.date(Analysis.analyzed_at).label("d"),
                func.coalesce(func.sum(Analysis.total_calories), 0.0).label("c"),
            )
            .filter(Analysis.user_id == user_id, Analysis.analyzed_at >= start)
            .group_by("d")
            .order_by("d")
            .all()
        )
        return [{"date": str(r.d), "calories": float(r.c)} for r in rows]
