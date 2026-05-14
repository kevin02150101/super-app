"""AI Service — the single module wrapping the Google Gemini API.

Strict rules:
- No Ollama.
- No local models (including gemma4:e2b and similar).
- The API key must come from the GEMINI_API_KEY environment variable (.env).
"""
import os
import json
import re
from typing import Any

from errors import MyCamError

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None


_PROMPT = (
    "You are a professional dietitian and food-image recognition expert.\n"
    "Identify every food item in the image and estimate its calories (kcal) and the three macros (grams) "
    "for each, plus an overall dietary summary and health tips.\n"
    "Use one of these for `category`: Staple / Protein / Vegetable / Fruit / Drink / Dessert / Other.\n"
    "`confidence` is a number between 0 and 1.\n"
    "If the image contains no food, return an empty `items` array with total_calories=0, "
    "set `summary` to \"No food detected\", and give general dietary advice in `health_advice`.\n\n"
    "Return **only** JSON in the schema below — no other text, Markdown, or comments:\n"
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


class AIService:
    _configured = False

    @classmethod
    def _ensure_configured(cls):
        if cls._configured:
            return
        if genai is None:
            raise MyCamError("AI_NO_SDK", "google-generativeai is not installed", 500)
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise MyCamError("AI_NO_KEY", "GEMINI_API_KEY is not set", 500)
        genai.configure(api_key=api_key)
        cls._configured = True

    @classmethod
    def analyze_food(cls, image_bytes: bytes, mime: str = "image/jpeg") -> dict[str, Any]:
        cls._ensure_configured()
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
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
        except MyCamError:
            raise
        except Exception as e:
            raise MyCamError("AI_FAIL", f"Gemini Analysis failed: {e}", 502)

        text = (getattr(resp, "text", "") or "").strip()
        if not text:
            raise MyCamError("AI_FAIL", "Gemini Empty response", 502)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Fallback: extract the {...} block
            m = re.search(r"\{.*\}", text, re.S)
            if not m:
                raise MyCamError("AI_BAD_JSON", "Gemini Response is not valid JSON", 502)
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError as e:
                raise MyCamError("AI_BAD_JSON", f"JSON Parse failed: {e}", 502)

        return cls._normalize(data)

    @staticmethod
    def _normalize(data: dict) -> dict:
        items = data.get("items") or []
        norm_items = []
        for it in items:
            if not isinstance(it, dict):
                continue
            norm_items.append({
                "name": str(it.get("name") or "Unknown"),
                "category": str(it.get("category") or "Other"),
                "calories": float(it.get("calories") or 0),
                "protein_g": _f(it.get("protein_g")),
                "fat_g": _f(it.get("fat_g")),
                "carbs_g": _f(it.get("carbs_g")),
                "confidence": _f(it.get("confidence")),
            })
        total = data.get("total_calories")
        try:
            total = float(total) if total is not None else sum(i["calories"] for i in norm_items)
        except (TypeError, ValueError):
            total = sum(i["calories"] for i in norm_items)

        return {
            "items": norm_items,
            "total_calories": total,
            "summary": str(data.get("summary") or ""),
            "health_advice": str(data.get("health_advice") or ""),
        }


def _f(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
