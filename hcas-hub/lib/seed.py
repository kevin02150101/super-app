"""Loader for HCAS seed data + helpers.

Lunch menus are keyed by ISO date string ("2026-05-11"). today_key() returns
the closest in-menu weekday so the app gracefully shows Monday on a Saturday.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

SEED_PATH = Path(__file__).parent.parent / "data" / "hcas_seed.json"


def load() -> dict:
    with open(SEED_PATH) as f:
        return json.load(f)


def today_key(now: datetime | None = None) -> str:
    """Return today's date as YYYY-MM-DD."""
    return (now or datetime.now()).strftime("%Y-%m-%d")


def closest_menu_date(menus: dict, now: datetime | None = None) -> str:
    """Pick the menu date to show by default.

    Order of preference:
    1. Today, if there's a menu.
    2. Next school day with a menu (within 14 days).
    3. Most recent past menu.
    4. Whatever the first key in the menu is.
    """
    now = now or datetime.now()
    today = now.date()
    today_iso = today.isoformat()
    if today_iso in menus:
        return today_iso

    # Look forward for the next school day
    for offset in range(1, 15):
        cand = (today + timedelta(days=offset)).isoformat()
        if cand in menus:
            return cand

    # Look backward
    for offset in range(1, 31):
        cand = (today - timedelta(days=offset)).isoformat()
        if cand in menus:
            return cand

    return next(iter(menus.keys()))


def week_dates(d_iso: str, menus: dict) -> list[str]:
    """Return all menu dates in the same Mon-Fri school week as d_iso."""
    d = datetime.strptime(d_iso, "%Y-%m-%d").date()
    monday = d - timedelta(days=d.weekday())
    week = []
    for i in range(5):  # Mon..Fri
        cand = (monday + timedelta(days=i)).isoformat()
        if cand in menus:
            week.append(cand)
    return week


def display_date(d_iso: str) -> str:
    """e.g., '2026-05-11' -> 'Mon May 11'."""
    d = datetime.strptime(d_iso, "%Y-%m-%d").date()
    return d.strftime("%a %b %-d")


def short_weekday(d_iso: str) -> str:
    """e.g., 'Mon'."""
    d = datetime.strptime(d_iso, "%Y-%m-%d").date()
    return d.strftime("%a")


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def is_today(s: str | None, now: datetime | None = None) -> bool:
    dt = parse_dt(s)
    if not dt:
        return False
    n = now or datetime.now()
    return dt.date() == n.date()


def humanize_dt(s: str | None) -> str:
    dt = parse_dt(s)
    if not dt:
        return ""
    now = datetime.now()
    if dt.date() == now.date():
        return f"Today {dt.strftime('%-I:%M %p')}"
    if (dt.date() - now.date()).days == 1:
        return f"Tomorrow {dt.strftime('%-I:%M %p')}"
    return dt.strftime("%a %b %-d · %-I:%M %p")
