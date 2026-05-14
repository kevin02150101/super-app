"""Streak service: heartbeat → milestone unlock → activity log."""
from __future__ import annotations

from datetime import date, timedelta

from . import db


def heartbeat(user_id: str, source: str = "web") -> dict:
    """Record today's login and process any newly-earned milestones.

    Returns:
        {
            "streak": { current_count, longest_count, last_login_date, delta },
            "newly_unlocked": [ {milestone, theme_code?} ]
        }
    """
    result = db.record_daily_login(user_id, source=source)
    current = result["current_count"]

    newly = []
    if result["delta"] != "unchanged":
        db.log_activity(user_id, "login",
                        {"streak": current, "delta": result["delta"]})
        if result["delta"] == "reset" and current == 1:
            db.log_activity(user_id, "streak_break", {})

        for ms in db.list_milestones():
            if current >= ms["threshold_days"]:
                claimed = db.claim_milestone(user_id, ms["id"])
                if not claimed:
                    continue
                payload = ms["reward_payload"] or {}
                entry: dict = {"milestone": ms["code"],
                               "threshold_days": ms["threshold_days"]}
                if ms["reward_type"] == "theme":
                    code = payload.get("theme_code")
                    theme = db.get_theme_by_code(code) if code else None
                    if theme:
                        db.unlock_theme(user_id, theme["id"], source="milestone")
                        entry["theme_code"] = code
                db.log_activity(user_id, "milestone_unlocked", entry)
                newly.append(entry)

    return {"streak": result, "newly_unlocked": newly}


def streak_history(user_id: str, days: int = 30) -> list[dict]:
    """Returns list of {date, present} for the last `days` days (oldest first)."""
    end = date.today()
    start = end - timedelta(days=days - 1)
    seen = set(db.login_history(user_id,
                                start.isoformat(),
                                end.isoformat()))
    out = []
    cur = start
    while cur <= end:
        iso = cur.isoformat()
        out.append({"date": iso, "present": iso in seen})
        cur += timedelta(days=1)
    return out
