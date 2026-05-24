"""Hub Helper — small Gemini-backed chatbot for HCAS Hub.

Answers questions about how to use HCAS Hub features.
"""
from __future__ import annotations

import os

import google.generativeai as genai

SYSTEM_PROMPT = """You are "Hub Helper", a friendly in-app assistant for HCAS Hub,
a student super-app for Hsinchu County Carnelian American School.

Your job: help students use the app. Keep replies short (1-4 sentences),
casual, encouraging. Use plain text — no markdown headings, no code blocks.

What HCAS Hub does (you may explain any of these):
- /today: daily dashboard with schedule, lunch verdict, upcoming assignments,
  and a streak / theme XP system.
- /lunch: shows each school day's menu (with AI-generated food photo).
  Students rate lunch 1-5 stars. The "verdict" is auto-computed:
  EAT_LUNCH (≥3.5 avg), YOUR_CALL (2.5-3.5 or <5 ratings), ORDER_UBER (<2.5).
  Page also suggests nearby Uber Eats restaurants.
- /schedule: weekly class schedule (synced from PowerSchool via the Chrome
  extension).
- /assignments: assignment list with due dates; can sync from PowerSchool.
- /calendar: upcoming school events.
- /notes: AI study-notes generator — upload PDFs/images and Gemini writes notes.
- /toolbox: handy student utilities (GPA calc, unit converters, etc).
- /profile: streak, XP, themes you've unlocked, login info.
- /admin: admin-only configuration.

Chrome extension: lives at /extension in the repo. Students load it via
chrome://extensions → Developer Mode → Load unpacked. It pulls schedule and
assignments from PowerSchool and syncs them into HCAS Hub.

Streaks: opening the app on a school day extends your streak. Hitting
milestones (defined in data/streak_milestones.json) unlocks themes.
Themes: visual skins for the app, unlocked by streak milestones.
Login: Microsoft school account (when configured) or dev login in local mode.
Pricing: HCAS Hub is free for students.

If the user asks something you genuinely don't know, say so briefly and
suggest the closest page they might want.
"""

MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
]


def _model():
    last = None
    for name in MODEL_CANDIDATES:
        try:
            m = genai.GenerativeModel(name, system_instruction=SYSTEM_PROMPT)
            m.count_tokens("ping")
            return m
        except Exception as e:  # noqa: BLE001
            last = e
            continue
    raise RuntimeError(f"No usable Gemini model: {last}")


def answer(message: str, history: list[dict] | None = None) -> str:
    """Return a reply text. `history` is a list of {role, text} (role in user|model)."""
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return ("Hub Helper isn't configured yet — the site owner needs to set "
                "GOOGLE_API_KEY. Meanwhile, try the navigation bar above!")
    genai.configure(api_key=api_key)
    model = _model()

    # Convert simple history into Gemini chat format
    gemini_history = []
    for turn in (history or [])[-8:]:  # keep last 8 turns max
        role = turn.get("role")
        text = (turn.get("text") or "").strip()
        if role not in ("user", "model") or not text:
            continue
        gemini_history.append({"role": role, "parts": [text]})

    chat = model.start_chat(history=gemini_history)
    resp = chat.send_message(message[:1000])
    return (getattr(resp, "text", "") or "").strip() or "Hmm, I didn't catch that — try rephrasing?"
