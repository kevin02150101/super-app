"""Textbook summary service — calls Gemini REST API and returns text + chart."""
from __future__ import annotations

import json
import re
from typing import Any

import requests
from flask import current_app

from ..models.summary_record import SummaryRecord
from ..repositories.summary_repository import SummaryRepository


class SummaryError(Exception):
    def __init__(self, message: str, status: int = 500) -> None:
        super().__init__(message)
        self.status = status


class SummaryValidationError(SummaryError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status=400)


class SummaryConfigurationError(SummaryError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status=503)


class SummaryProviderError(SummaryError):
    def __init__(self, message: str, status: int = 502) -> None:
        super().__init__(message, status=status)


class SummaryService:
    """Generates an English study summary plus a small chart using Gemini."""

    def generate(self, keyword: str) -> dict:
        keyword = self._normalize_keyword(keyword)

        api_key = (current_app.config.get("GEMINI_API_KEY") or "").strip()
        if not api_key:
            raise SummaryConfigurationError(
                "GEMINI_API_KEY is not set. Please edit .env and restart the server."
            )

        model = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")
        url_template = current_app.config["GEMINI_API_URL"]
        timeout = current_app.config.get("REQUEST_TIMEOUT", 30)

        prompt = self._build_prompt(keyword)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "topP": 0.9,
                "maxOutputTokens": 2000,
                "responseMimeType": "application/json",
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
            raise SummaryProviderError(
                f"Gemini API error: {self._error_detail(exc.response)}"
            ) from exc
        except requests.RequestException as exc:
            raise SummaryProviderError("Cannot reach Gemini API. Please try again.") from exc

        text = self._extract_text(resp.json())
        if not text:
            raise SummaryProviderError("Gemini returned empty content.")

        summary_text, graph = self._parse_payload(text)

        record = SummaryRecord(
            keyword=keyword,
            summary_text=summary_text,
            chart_data=json.dumps(graph, ensure_ascii=False) if graph else None,
            source_model=model,
        )
        SummaryRepository.create(record)
        return record.to_dict()

    def history(self, limit: int = 30) -> list[dict]:
        return [r.to_dict() for r in SummaryRepository.list_recent(limit)]

    def get(self, record_id: int) -> dict | None:
        r = SummaryRepository.get(record_id)
        return r.to_dict() if r else None

    # ---- helpers ----
    def _normalize_keyword(self, keyword: str) -> str:
        kw = str(keyword or "").strip()
        if not kw:
            raise SummaryValidationError(
                "Please enter a topic keyword, e.g. AI, photosynthesis, cell division."
            )
        max_len = current_app.config.get("MAX_KEYWORD_LENGTH", 80)
        if len(kw) > max_len:
            raise SummaryValidationError(
                f"Keyword cannot exceed {max_len} characters."
            )
        return kw

    def _build_prompt(self, keyword: str) -> str:
        return "\n".join(
            [
                f'You are a clear, structured study tutor. Topic keyword: "{keyword}".',
                "Audience: middle-school to early-college students.",
                "Write the entire response in ENGLISH only.",
                "",
                "Return ONLY a JSON object (no markdown fence) matching exactly:",
                "{",
                '  "summary_text": "A multi-paragraph study summary in Markdown.',
                '    Include: (1) a 2-3 sentence overview,',
                '    (2) 3-5 key concept sections with `## headings`,',
                '    (3) common applications and exam pitfalls,',
                '    (4) a final ## Key Takeaways section.",',
                '  "graph": {',
                '    "title": "Short concept-graph title (English, max 60 chars)",',
                '    "nodes": [',
                '       {"id": "n1", "label": "Central topic", "group": "core"},',
                '       {"id": "n2", "label": "Subtopic A",   "group": "concept"},',
                '       {"id": "n3", "label": "Subtopic B",   "group": "concept"},',
                '       {"id": "n4", "label": "Example / Application", "group": "example"}',
                '    ],',
                '    "edges": [',
                '       {"source": "n1", "target": "n2", "label": "includes"},',
                '       {"source": "n1", "target": "n3", "label": "relates to"},',
                '       {"source": "n2", "target": "n4", "label": "example"}',
                '    ]',
                "  }",
                "}",
                "",
                "Graph rules:",
                " - Build a concept map / knowledge graph about the topic.",
                " - 5-10 nodes total. The FIRST node must be the central topic with group=\"core\".",
                " - Other groups: \"concept\" (key idea), \"example\" (concrete example/application),",
                "   \"caveat\" (common pitfall/misconception).",
                " - 5-12 edges. Every node must be connected. Edge labels are short verbs/phrases (max 20 chars).",
                " - Node labels are short (max 28 chars).",
                " - Node ids are unique strings; edge source/target must reference existing node ids.",
                "Do NOT wrap the JSON in ``` fences. Output raw JSON only.",
            ]
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
    def _parse_payload(text: str) -> tuple[str, dict | None]:
        """Try to parse JSON {summary_text, chart}; fall back to raw text."""
        cleaned = text.strip()
        # strip optional ```json ... ``` fences
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", cleaned, re.S)
            if not m:
                return text, None
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                return text, None

        if not isinstance(data, dict):
            return text, None

        summary_text = str(data.get("summary_text") or text).strip()
        graph_raw = data.get("graph") or data.get("concept_graph")
        graph = None
        if isinstance(graph_raw, dict):
            raw_nodes = graph_raw.get("nodes") or []
            raw_edges = graph_raw.get("edges") or graph_raw.get("links") or []
            nodes: list[dict] = []
            seen_ids: set[str] = set()
            if isinstance(raw_nodes, list):
                for i, n in enumerate(raw_nodes):
                    if not isinstance(n, dict):
                        continue
                    nid = str(n.get("id") or f"n{i+1}").strip()
                    label = str(n.get("label") or nid).strip()[:60]
                    group = str(n.get("group") or "concept").lower()
                    if group not in ("core", "concept", "example", "caveat"):
                        group = "concept"
                    if nid and nid not in seen_ids and label:
                        nodes.append({"id": nid, "label": label, "group": group})
                        seen_ids.add(nid)
            edges: list[dict] = []
            if isinstance(raw_edges, list):
                for e in raw_edges:
                    if not isinstance(e, dict):
                        continue
                    src = str(e.get("source") or e.get("from") or "").strip()
                    tgt = str(e.get("target") or e.get("to") or "").strip()
                    if src in seen_ids and tgt in seen_ids and src != tgt:
                        edges.append({
                            "source": src,
                            "target": tgt,
                            "label": str(e.get("label") or "")[:30],
                        })
            if nodes:
                graph = {
                    "title": str(graph_raw.get("title") or "Concept graph")[:120],
                    "nodes": nodes,
                    "edges": edges,
                }
        return summary_text, graph

    @staticmethod
    def _error_detail(resp) -> str:
        if resp is None:
            return "unknown error"
        try:
            data = resp.json()
            return data.get("error", {}).get("message") or resp.text
        except Exception:
            return resp.text or "unknown error"
