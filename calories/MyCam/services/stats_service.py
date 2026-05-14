from repositories.analysis_repository import AnalysisRepository
from repositories.food_item_repository import FoodItemRepository


class StatsService:
    @staticmethod
    def kpi_summary(user_id: int) -> dict:
        return {
            "today_calories": AnalysisRepository.sum_calories_today(user_id),
            "total_count": AnalysisRepository.count(user_id),
            "top_food": FoodItemRepository.top_food(user_id),
        }

    @staticmethod
    def calories_timeseries(user_id: int, days: int = 30):
        return AnalysisRepository.daily_calories(user_id, days=days)

    @staticmethod
    def category_distribution(user_id: int):
        return FoodItemRepository.category_distribution(user_id)
