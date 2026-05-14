"""Theme service: lists themes with per-user lock status, activates a theme."""
from __future__ import annotations

from fastapi import HTTPException

from . import db


def list_for_user(user_id: str) -> list[dict]:
    """Return all active themes with `unlocked` and `active` flags."""
    prefs = db.get_preferences(user_id)
    active_id = prefs.get("active_theme_id")
    unlocked = set(db.list_user_unlocks(user_id))
    out = []
    for t in db.list_themes():
        rule = t.get("unlock_rule") or {}
        is_default = rule.get("type") == "default"
        is_unlocked = is_default or t["id"] in unlocked
        out.append({
            "id": t["id"],
            "code": t["code"],
            "name": t["name"],
            "palette": t["palette"],
            "font": t["font"],
            "preview_emoji": t["preview_emoji"],
            "unlock_rule": rule,
            "unlocked": is_unlocked,
            "active": t["id"] == active_id,
        })
    return out


def activate(user_id: str, theme_code: str) -> dict:
    theme = db.get_theme_by_code(theme_code)
    if not theme:
        raise HTTPException(404, f"unknown theme: {theme_code}")
    rule = theme["unlock_rule"] or {}
    is_default = rule.get("type") == "default"
    if not is_default and theme["id"] not in set(db.list_user_unlocks(user_id)):
        raise HTTPException(403, f"theme '{theme_code}' is locked")
    db.set_active_theme(user_id, theme["id"])
    db.log_activity(user_id, "theme_changed", {"theme_code": theme_code})
    return theme
