import json

from services.image_service import ImageService
from services.ai_service import AIService
from repositories.analysis_repository import AnalysisRepository
from repositories.food_item_repository import FoodItemRepository


class AnalysisService:
    @staticmethod
    def analyze(user_id: int, file_storage):
        rel_path, image_bytes, mime = ImageService.save_and_preprocess(user_id, file_storage)
        result = AIService.analyze_food(image_bytes, mime=mime)

        analysis = AnalysisRepository.create(
            user_id=user_id,
            image_path=rel_path,
            total_calories=result["total_calories"],
            summary=result["summary"],
            health_advice=result["health_advice"],
            raw_json=json.dumps(result, ensure_ascii=False),
        )
        if result["items"]:
            FoodItemRepository.bulk_create(analysis.id, result["items"])
        # refresh
        return AnalysisRepository.get_for_user(analysis.id, user_id)

    @staticmethod
    def list(user_id: int, page: int = 1, per_page: int = 20):
        return AnalysisRepository.paginate(user_id, page=page, per_page=per_page)

    @staticmethod
    def get(user_id: int, analysis_id: int):
        return AnalysisRepository.get_for_user(analysis_id, user_id)

    @staticmethod
    def delete(user_id: int, analysis_id: int) -> bool:
        return AnalysisRepository.delete_for_user(analysis_id, user_id)
