"""Thin wrapper around the Supabase Python client.

Reads SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from env. The service-role key
bypasses Row Level Security and must never be exposed to the browser — keep
it in Render/host env vars only.

If either env var is missing, `client()` returns None so the rest of the app
keeps working (Supabase features just become no-ops).
"""
from __future__ import annotations
import os
from typing import Optional

_CACHED = None


def is_enabled() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))


def client() -> Optional[object]:
    global _CACHED
    if _CACHED is not None:
        return _CACHED
    if not is_enabled():
        return None
    try:
        from supabase import create_client  # lazy import
    except Exception:
        return None
    _CACHED = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )
    return _CACHED


# ---------- notes_history helpers ----------
def save_note(*, user_id: str | None, topic: str, content: str,
              attachments: list[str] | None = None) -> dict | None:
    sb = client()
    if not sb:
        return None
    row = {
        "user_id": user_id,
        "topic": (topic or "")[:200],
        "content": content,
        "attachments": attachments or [],
    }
    try:
        res = sb.table("note_history").insert(row).execute()
        return (res.data or [None])[0]
    except Exception:
        return None


def list_notes(user_id: str | None, limit: int = 10) -> list[dict]:
    sb = client()
    if not sb:
        return []
    try:
        q = sb.table("note_history").select("id, topic, created_at").order(
            "created_at", desc=True).limit(limit)
        if user_id:
            q = q.eq("user_id", user_id)
        else:
            q = q.is_("user_id", None)
        res = q.execute()
        return res.data or []
    except Exception:
        return []


def get_note(note_id: str) -> dict | None:
    sb = client()
    if not sb:
        return None
    try:
        res = sb.table("note_history").select("*").eq("id", note_id).limit(1).execute()
        return (res.data or [None])[0]
    except Exception:
        return None
