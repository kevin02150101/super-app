"""Vibe Spec 產生 Service — 移植自 vibespec-generator/services/geminiService.ts。

把使用者輸入的「點子 + 技術棧偏好」交給 Gemini,產生完整 Markdown 技術規格書。
"""
from __future__ import annotations

import json
from typing import Any

import requests
from flask import current_app

from ..models.vibespec_record import VibeSpecRecord
from ..repositories.vibespec_repository import VibeSpecRepository


class VibeSpecError(Exception):
    def __init__(self, message: str, status: int = 500) -> None:
        super().__init__(message)
        self.status = status


class VibeSpecValidationError(VibeSpecError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status=400)


class VibeSpecConfigurationError(VibeSpecError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status=503)


class VibeSpecProviderError(VibeSpecError):
    def __init__(self, message: str, status: int = 502) -> None:
        super().__init__(message, status=status)


_SYSTEM_INSTRUCTION = (
    "You are a world-class senior software architect and Vibe Coding expert.\n"
    "The user wants a high-quality Technical Specification document so that "
    "AI coding assistants (Cursor, Windsurf, Replit, Copilot) can execute development precisely.\n"
    "Output must be ENGLISH, pure Markdown, well-structured and professional in tone."
)


class VibeSpecService:
    def generate(self, idea: str, tech_stack: dict | None = None) -> dict:
        idea = (idea or "").strip()
        if not idea:
            raise VibeSpecValidationError("Please describe your idea or product vision.")

        api_key = (current_app.config.get("GEMINI_API_KEY") or "").strip()
        if not api_key:
            raise VibeSpecConfigurationError("GEMINI_API_KEY is not set. Please edit .env.")

        model = current_app.config.get("GEMINI_MODEL", "gemini-2.0-flash")
        url_template = current_app.config["GEMINI_API_URL"]
        timeout = current_app.config.get("REQUEST_TIMEOUT", 60)

        tech_stack = tech_stack or {
            "frontend": "React (Vite)",
            "ui": "Bootstrap 5.3 + Vue / Shadcn UI + Tailwind",
            "api": "Python (Flask)",
            "database": "SQLite / PostgreSQL",
            "infrastructure": "Docker (Self-host)",
            "aiProvider": "Gemini API",
        }

        prompt = self._build_prompt(idea, tech_stack)
        payload = {
            "system_instruction": {"parts": [{"text": _SYSTEM_INSTRUCTION}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.5,
                "topP": 0.9,
                "maxOutputTokens": 4000,
            },
        }

        try:
            resp = requests.post(
                url_template.format(model=model),
                params={"key": api_key},
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
        except requests.HTTPError as exc:
            raise VibeSpecProviderError(
                f"Gemini API error: {self._error_detail(exc.response)}"
            ) from exc
        except requests.RequestException as exc:
            raise VibeSpecProviderError("Cannot reach Gemini API. Please try again.") from exc

        text = self._extract_text(resp.json())
        if not text:
            raise VibeSpecProviderError("Gemini returned empty content.")

        record = VibeSpecRecord(
            idea=idea,
            tech_stack=json.dumps(tech_stack, ensure_ascii=False),
            spec_markdown=text,
            source_model=model,
        )
        VibeSpecRepository.create(record)
        return record.to_dict()

    def history(self, limit: int = 30) -> list[dict]:
        return [r.to_dict() for r in VibeSpecRepository.list_recent(limit)]

    def get(self, record_id: int) -> dict | None:
        r = VibeSpecRepository.get(record_id)
        return r.to_dict() if r else None

    # ---- helpers ----
    def _build_prompt(self, idea: str, tech: dict) -> str:
        tech_json = json.dumps(tech, ensure_ascii=False, indent=2)
        return (
            f"Expand the following user idea and tech stack preferences into a complete "
            f"Technical Specification document:\n\n"
            f"User idea:\n{idea}\n\n"
            f"Tech stack preferences:\n{tech_json}\n\n"
            "Output ENGLISH, pure Markdown, with the following sections:\n"
            "1. **Project Vision & Core Value** — concise project goals.\n"
            "2. **Functional Requirements** — concrete modules and business logic.\n"
            "3. **UI Specification** — layout, colour palette, responsive behaviour.\n"
            f"4. **Tech Stack & Implementation Strategy** — concrete advice for {tech.get('frontend')} and {tech.get('api')}.\n"
            "5. **Data Schema** — structured table definitions.\n"
            "6. **Vibe Coding Prompt Sequence** — 3-5 ready-to-paste prompts for AI coding assistants.\n\n"
            "Tone: professional, clear, extremely AI-coding-assistant-friendly."
        )

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        parts: list[str] = []
        for cand in payload.get("candidates", []):
            for part in (cand.get("content") or {}).get("parts", []):
                t = part.get("text")
                if t:
                    parts.append(t.strip())
        return "\n\n".join(parts)

    @staticmethod
    def _error_detail(resp) -> str:
        if resp is None:
            return "unknown error"
        try:
            data = resp.json()
            return data.get("error", {}).get("message") or resp.text
        except Exception:
            return resp.text or "unknown error"
