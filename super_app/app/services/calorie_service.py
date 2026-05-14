"""卡路里 AI Service — 完整移植自 MyCam,以 Google Gemini 分析食物影像。

嚴格限制(同 MyCam):
- 僅使用 Google Gemini API。
- API Key 來自環境變數 GEMINI_API_KEY。
"""
from __future__ import annotations

import io
import json
import os
import re
import uuid
from datetime import datetime
from typing import Any

from flask import current_app
from PIL import Image

from ..extensions import db
from ..repositories.calorie_repository import AnalysisRepository, FoodItemRepository

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None


class CalorieError(Exception):
    def __init__(self, code: str, message: str, status: int = 500) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


_PROMPT = (
    "You are a professional nutritionist and food image recognition expert.\n"
    "Identify every food item in the image and estimate, for each item, its calories (kcal) "
    "and the three main macronutrients (in grams). Also provide an overall summary and a "
    "health advice line.\n"
    "Use these `category` values only: Staple / Protein / Vegetable / Fruit / Beverage / "
    "Dessert / Other.\n"
    "`confidence` is a number between 0 and 1.\n"
    "If no food is present, return items=[] and total_calories=0, summary='No food detected', "
    "and a generic dietary advice as health_advice.\n\n"
    "Return **only** the following JSON, no markdown, no commentary:\n"
    "{\n"
    '  "items": [\n'
    '    {"name": str, "category": str, "calories": number,\n'
    '     "protein_g": number, "fat_g": number, "carbs_g": number,\n'
    '     "confidence": number}\n'
    "  ],\n"
    '  "total_calories": number,\n'
    '  "summary": str,\n'
    '  "health_advice": str\n'
    "}"
)


def _to_float(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


class ImageService:
    """負責儲存上傳影像並轉為 JPEG(壓縮、修正方向)。"""

    @staticmethod
    def save_and_preprocess(file_storage) -> tuple[str, bytes, str]:
        if not file_storage or not file_storage.filename:
            raise CalorieError("NO_IMAGE", "No image uploaded", 400)

        raw = file_storage.read()
        if not raw:
            raise CalorieError("EMPTY_IMAGE", "Uploaded image is empty", 400)

        try:
            img = Image.open(io.BytesIO(raw))
            img.load()
        except Exception as exc:  # noqa: BLE001
            raise CalorieError("BAD_IMAGE", f"Cannot decode image: {exc}", 400) from exc

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 縮圖(最長邊 1280px)
        max_side = 1280
        if max(img.size) > max_side:
            ratio = max_side / max(img.size)
            img = img.resize(
                (int(img.size[0] * ratio), int(img.size[1] * ratio)),
                Image.Resampling.LANCZOS,
            )

        # 序列化為 JPEG
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88)
        jpeg_bytes = buf.getvalue()

        # 儲存到 static/uploads
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
        full_path = os.path.join(upload_folder, filename)
        with open(full_path, "wb") as fp:
            fp.write(jpeg_bytes)

        rel_path = f"uploads/{filename}"  # 用於 url_for static
        return rel_path, jpeg_bytes, "image/jpeg"


class AIService:
    """唯一封裝 Google Gemini API 的模組。"""

    _configured = False

    @classmethod
    def _ensure_configured(cls) -> None:
        if cls._configured:
            return
        if genai is None:
            raise CalorieError("AI_NO_SDK", "google-generativeai is not installed", 500)
        api_key = (current_app.config.get("GEMINI_API_KEY") or "").strip()
        if not api_key:
            raise CalorieError(
                "AI_NO_KEY",
                "GEMINI_API_KEY is not set (please edit .env)",
                500,
            )
        genai.configure(api_key=api_key)
        cls._configured = True

    @classmethod
    def analyze_food(cls, image_bytes: bytes, mime: str = "image/jpeg") -> dict[str, Any]:
        cls._ensure_configured()
        model_name = current_app.config.get("GEMINI_VISION_MODEL", "gemini-2.0-flash")
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content(
                [
                    _PROMPT,
                    {"mime_type": mime, "data": image_bytes},
                ],
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                },
            )
        except CalorieError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise CalorieError("AI_FAIL", f"Gemini analysis failed: {exc}", 502) from exc

        text = (getattr(resp, "text", "") or "").strip()
        if not text:
            raise CalorieError("AI_FAIL", "Gemini returned empty response", 502)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.S)
            if not m:
                raise CalorieError("AI_BAD_JSON", "Gemini response is not valid JSON", 502)
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError as exc:
                raise CalorieError(
                    "AI_BAD_JSON", f"JSON parse failed: {exc}", 502
                ) from exc

        return cls._normalize(data)

    @staticmethod
    def _normalize(data: dict) -> dict:
        items = data.get("items") or []
        norm_items = []
        for it in items:
            if not isinstance(it, dict):
                continue
            norm_items.append(
                {
                    "name": str(it.get("name") or "Unknown"),
                    "category": str(it.get("category") or "Other"),
                    "calories": float(it.get("calories") or 0),
                    "protein_g": _to_float(it.get("protein_g")),
                    "fat_g": _to_float(it.get("fat_g")),
                    "carbs_g": _to_float(it.get("carbs_g")),
                    "confidence": _to_float(it.get("confidence")),
                }
            )
        total = data.get("total_calories")
        try:
            total = (
                float(total) if total is not None else sum(i["calories"] for i in norm_items)
            )
        except (TypeError, ValueError):
            total = sum(i["calories"] for i in norm_items)

        return {
            "items": norm_items,
            "total_calories": total,
            "summary": str(data.get("summary") or ""),
            "health_advice": str(data.get("health_advice") or ""),
        }


class AnalysisService:
    @staticmethod
    def analyze(file_storage) -> dict:
        rel_path, image_bytes, mime = ImageService.save_and_preprocess(file_storage)
        result = AIService.analyze_food(image_bytes, mime=mime)

        analysis = AnalysisRepository.create(
            image_path=rel_path,
            total_calories=result["total_calories"],
            summary=result["summary"],
            health_advice=result["health_advice"],
            raw_json=json.dumps(result, ensure_ascii=False),
        )
        if result["items"]:
            FoodItemRepository.bulk_create(analysis.id, result["items"])
        db.session.refresh(analysis)
        return analysis.to_dict()

    @staticmethod
    def list_recent(limit: int = 30) -> list[dict]:
        return [a.to_dict(include_items=False) for a in AnalysisRepository.list_recent(limit)]

    @staticmethod
    def get(analysis_id: int) -> dict | None:
        a = AnalysisRepository.get(analysis_id)
        return a.to_dict() if a else None

    @staticmethod
    def delete(analysis_id: int) -> bool:
        return AnalysisRepository.delete(analysis_id)
