"""SQLite storage for HCAS Hub.

Originally just ratings + assignments. Now extended (per PRD) to support:
- users / sessions / oauth_tokens (Microsoft OAuth2-ready)
- user_streaks / login_events / streak_milestones / user_milestones
- themes / user_unlocks / user_preferences
- activity_events (history & analytics stream)

The schema stays SQLite for zero-setup dev parity with the rest of HCAS Hub,
but mirrors the target PostgreSQL DDL in PRD.md (TEXT-as-UUID, JSON-as-TEXT),
so the production migration is mechanical.
"""
import sqlite3
import json
import secrets
import hashlib
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

DB_PATH = Path(__file__).parent.parent / "data" / "hub.db"
SCHOOL_TZ = ZoneInfo("Asia/Taipei")


def conn():
    c = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


def school_today() -> str:
    """Date in school timezone, ISO format (used for streak math)."""
    return datetime.now(SCHOOL_TZ).date().isoformat()


# ──────────────────────────────────────────────────────────────────────────
# Schema
# ──────────────────────────────────────────────────────────────────────────
def init():
    DB_PATH.parent.mkdir(exist_ok=True)
    with conn() as c:
        # ── legacy core tables (kept as-is for back-compat) ────────────
        c.executescript("""
        CREATE TABLE IF NOT EXISTS lunch_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            stars INTEGER NOT NULL,
            comment TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT,
            due_at TEXT,
            done INTEGER NOT NULL DEFAULT 0,
            priority INTEGER DEFAULT 99,
            source TEXT DEFAULT 'manual',
            external_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)

        cols = {row["name"] for row in c.execute("PRAGMA table_info(assignments)")}
        if "source" not in cols:
            c.execute("ALTER TABLE assignments ADD COLUMN source TEXT DEFAULT 'manual'")
        if "external_id" not in cols:
            c.execute("ALTER TABLE assignments ADD COLUMN external_id TEXT")
        if "updated_at" not in cols:
            c.execute("ALTER TABLE assignments ADD COLUMN updated_at TEXT")
        if "user_id" not in cols:
            c.execute("ALTER TABLE assignments ADD COLUMN user_id TEXT")

        rcols = {row["name"] for row in c.execute("PRAGMA table_info(lunch_ratings)")}
        if "user_id" not in rcols:
            c.execute("ALTER TABLE lunch_ratings ADD COLUMN user_id TEXT")

        c.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_assignments_external "
            "ON assignments(source, external_id) WHERE external_id IS NOT NULL"
        )

        # ── new tables (PRD §5) ─────────────────────────────────────────
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            TEXT PRIMARY KEY,
            email         TEXT UNIQUE NOT NULL,
            display_name  TEXT NOT NULL,
            avatar_url    TEXT,
            ms_oid        TEXT UNIQUE,
            role          TEXT NOT NULL DEFAULT 'student',
            created_at    TEXT NOT NULL DEFAULT (datetime('now')),
            last_login_at TEXT,
            deleted_at    TEXT
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash  TEXT NOT NULL UNIQUE,
            ip          TEXT,
            user_agent  TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at  TEXT NOT NULL,
            revoked_at  TEXT
        );
        CREATE INDEX IF NOT EXISTS ix_sessions_user ON sessions(user_id);

        CREATE TABLE IF NOT EXISTS oauth_tokens (
            user_id           TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            provider          TEXT NOT NULL DEFAULT 'microsoft',
            refresh_token_enc BLOB NOT NULL,
            refresh_token_iv  BLOB NOT NULL,
            scopes            TEXT NOT NULL,
            expires_at        TEXT NOT NULL,
            updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS user_streaks (
            user_id            TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            current_count      INTEGER NOT NULL DEFAULT 0,
            longest_count      INTEGER NOT NULL DEFAULT 0,
            last_login_date    TEXT,
            current_started_at TEXT,
            updated_at         TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS login_events (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            login_date TEXT NOT NULL,
            login_at   TEXT NOT NULL DEFAULT (datetime('now')),
            source     TEXT NOT NULL DEFAULT 'web',
            UNIQUE(user_id, login_date)
        );
        CREATE INDEX IF NOT EXISTS ix_login_user_date ON login_events(user_id, login_date DESC);

        CREATE TABLE IF NOT EXISTS streak_milestones (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            code           TEXT UNIQUE NOT NULL,
            threshold_days INTEGER NOT NULL,
            reward_type    TEXT NOT NULL,
            reward_payload TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS user_milestones (
            user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            milestone_id INTEGER NOT NULL REFERENCES streak_milestones(id),
            achieved_at  TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, milestone_id)
        );

        CREATE TABLE IF NOT EXISTS themes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            code          TEXT UNIQUE NOT NULL,
            name          TEXT NOT NULL,
            palette       TEXT NOT NULL,
            font          TEXT,
            preview_emoji TEXT,
            unlock_rule   TEXT NOT NULL,
            is_active     INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS user_unlocks (
            user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            theme_id    INTEGER NOT NULL REFERENCES themes(id),
            unlocked_at TEXT NOT NULL DEFAULT (datetime('now')),
            source      TEXT NOT NULL,
            PRIMARY KEY (user_id, theme_id)
        );

        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id          TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            active_theme_id  INTEGER REFERENCES themes(id),
            dashboard_layout TEXT NOT NULL DEFAULT '{}',
            badge_config     TEXT NOT NULL DEFAULT '{}',
            updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS activity_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            event_type  TEXT NOT NULL,
            payload     TEXT NOT NULL DEFAULT '{}',
            occurred_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS ix_activity_user_time
            ON activity_events(user_id, occurred_at DESC);
        CREATE INDEX IF NOT EXISTS ix_activity_user_type
            ON activity_events(user_id, event_type, occurred_at DESC);

        CREATE TABLE IF NOT EXISTS announcements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            body        TEXT NOT NULL DEFAULT '',
            tone        TEXT NOT NULL DEFAULT 'info',
            pinned      INTEGER NOT NULL DEFAULT 0,
            active      INTEGER NOT NULL DEFAULT 1,
            created_by  TEXT REFERENCES users(id) ON DELETE SET NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS ix_announcements_active
            ON announcements(active, pinned DESC, created_at DESC);

        CREATE TABLE IF NOT EXISTS class_schedule (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT REFERENCES users(id) ON DELETE CASCADE,
            course      TEXT NOT NULL,
            teacher     TEXT NOT NULL DEFAULT '',
            room        TEXT NOT NULL DEFAULT '',
            period      TEXT NOT NULL DEFAULT '',
            days        TEXT NOT NULL DEFAULT '',
            start_time  TEXT NOT NULL DEFAULT '',
            end_time    TEXT NOT NULL DEFAULT '',
            source      TEXT NOT NULL DEFAULT 'powerschool',
            external_id TEXT NOT NULL DEFAULT '',
            updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, external_id)
        );
        CREATE INDEX IF NOT EXISTS ix_schedule_user
            ON class_schedule(user_id, period, start_time);
        """)


# ──────────────────────────────────────────────────────────────────────────
# Seed helpers
# ──────────────────────────────────────────────────────────────────────────
def seed_milestones(rows: Iterable[dict]) -> None:
    with conn() as c:
        for r in rows:
            c.execute(
                "INSERT OR IGNORE INTO streak_milestones "
                "(code, threshold_days, reward_type, reward_payload) VALUES (?,?,?,?)",
                (r["code"], r["threshold_days"], r["reward_type"],
                 json.dumps(r["reward_payload"])),
            )


def seed_themes(rows: Iterable[dict]) -> None:
    with conn() as c:
        for r in rows:
            c.execute(
                "INSERT OR IGNORE INTO themes "
                "(code, name, palette, font, preview_emoji, unlock_rule) "
                "VALUES (?,?,?,?,?,?)",
                (r["code"], r["name"], json.dumps(r["palette"]),
                 r.get("font"), r.get("preview_emoji"),
                 json.dumps(r["unlock_rule"])),
            )


# ──────────────────────────────────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────────────────────────────────
def upsert_user(email: str, display_name: str,
                avatar_url: str | None = None, ms_oid: str | None = None,
                role: str = "student") -> dict:
    """Insert-or-update by (ms_oid if provided else email). Returns user row."""
    with conn() as c:
        row = None
        if ms_oid:
            row = c.execute("SELECT * FROM users WHERE ms_oid=?",
                            (ms_oid,)).fetchone()
        if not row:
            row = c.execute("SELECT * FROM users WHERE email=?",
                            (email,)).fetchone()
        if row:
            c.execute(
                "UPDATE users SET email=?, display_name=?, avatar_url=?, "
                "ms_oid=COALESCE(?, ms_oid), last_login_at=datetime('now'), "
                "deleted_at=NULL WHERE id=?",
                (email, display_name, avatar_url, ms_oid, row["id"]),
            )
            return dict(c.execute("SELECT * FROM users WHERE id=?",
                                  (row["id"],)).fetchone())
        uid = secrets.token_urlsafe(16)
        c.execute(
            "INSERT INTO users (id, email, display_name, avatar_url, ms_oid, "
            " role, last_login_at) VALUES (?,?,?,?,?,?,datetime('now'))",
            (uid, email, display_name, avatar_url, ms_oid, role),
        )
        return dict(c.execute("SELECT * FROM users WHERE id=?",
                              (uid,)).fetchone())


def get_user(user_id: str) -> dict | None:
    with conn() as c:
        row = c.execute(
            "SELECT * FROM users WHERE id=? AND deleted_at IS NULL", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def mark_last_login(user_id: str) -> None:
    with conn() as c:
        c.execute("UPDATE users SET last_login_at=datetime('now') WHERE id=?",
                  (user_id,))


def soft_delete_user(user_id: str) -> None:
    with conn() as c:
        c.execute("UPDATE users SET deleted_at=datetime('now') WHERE id=?",
                  (user_id,))


# ──────────────────────────────────────────────────────────────────────────
# Sessions  (opaque token; only SHA-256 hash stored in DB)
# ──────────────────────────────────────────────────────────────────────────
def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user_id: str, ip: str | None = None,
                   user_agent: str | None = None, ttl_days: int = 30) -> str:
    """Create a session row. Returns the opaque token (clients store this)."""
    token = secrets.token_urlsafe(32)
    sid = secrets.token_urlsafe(12)
    expires = (datetime.utcnow() + timedelta(days=ttl_days)).isoformat()
    with conn() as c:
        c.execute(
            "INSERT INTO sessions (id, user_id, token_hash, ip, user_agent, expires_at) "
            "VALUES (?,?,?,?,?,?)",
            (sid, user_id, _hash_token(token), ip, user_agent, expires),
        )
    return token


def session_user(token: str | None) -> dict | None:
    if not token:
        return None
    with conn() as c:
        row = c.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash=? AND s.revoked_at IS NULL "
            "AND s.expires_at > datetime('now') AND u.deleted_at IS NULL",
            (_hash_token(token),),
        ).fetchone()
    return dict(row) if row else None


def revoke_session(token: str | None) -> None:
    if not token:
        return
    with conn() as c:
        c.execute("UPDATE sessions SET revoked_at=datetime('now') WHERE token_hash=?",
                  (_hash_token(token),))


# ──────────────────────────────────────────────────────────────────────────
# OAuth tokens
# ──────────────────────────────────────────────────────────────────────────
def save_oauth_token(user_id: str, refresh_enc: bytes, iv: bytes,
                     scopes: list[str], expires_at_iso: str,
                     provider: str = "microsoft") -> None:
    with conn() as c:
        c.execute(
            "INSERT INTO oauth_tokens "
            "(user_id, provider, refresh_token_enc, refresh_token_iv, scopes, expires_at, updated_at) "
            "VALUES (?,?,?,?,?,?,datetime('now')) "
            "ON CONFLICT(user_id) DO UPDATE SET "
            "  refresh_token_enc=excluded.refresh_token_enc, "
            "  refresh_token_iv=excluded.refresh_token_iv, "
            "  scopes=excluded.scopes, "
            "  expires_at=excluded.expires_at, "
            "  updated_at=datetime('now')",
            (user_id, provider, refresh_enc, iv, " ".join(scopes), expires_at_iso),
        )


def get_oauth_token(user_id: str) -> dict | None:
    with conn() as c:
        row = c.execute("SELECT * FROM oauth_tokens WHERE user_id=?",
                        (user_id,)).fetchone()
    return dict(row) if row else None


# ──────────────────────────────────────────────────────────────────────────
# Streak / login events / milestones
# ──────────────────────────────────────────────────────────────────────────
def get_streak(user_id: str) -> dict:
    with conn() as c:
        row = c.execute(
            "SELECT * FROM user_streaks WHERE user_id=?", (user_id,)
        ).fetchone()
        if row:
            return dict(row)
        c.execute("INSERT INTO user_streaks (user_id) VALUES (?)", (user_id,))
    return {"user_id": user_id, "current_count": 0, "longest_count": 0,
            "last_login_date": None, "current_started_at": None}


def record_daily_login(user_id: str, today: str | None = None,
                       source: str = "web") -> dict:
    """Idempotent per (user_id, date).

    Returns the updated streak plus `delta`: 'unchanged' | 'incremented' | 'reset'.
    """
    today = today or school_today()
    with conn() as c:
        row = c.execute("SELECT * FROM user_streaks WHERE user_id=?",
                        (user_id,)).fetchone()
        if not row:
            c.execute("INSERT INTO user_streaks (user_id) VALUES (?)", (user_id,))
            row = c.execute("SELECT * FROM user_streaks WHERE user_id=?",
                            (user_id,)).fetchone()
        last = row["last_login_date"]
        current = row["current_count"] or 0
        longest = row["longest_count"] or 0
        started = row["current_started_at"]

        if last == today:
            delta = "unchanged"
        else:
            if last:
                last_d = date.fromisoformat(last)
                today_d = date.fromisoformat(today)
                if (today_d - last_d).days == 1:
                    current += 1
                    delta = "incremented"
                else:
                    current = 1
                    started = today
                    delta = "reset"
            else:
                current = 1
                started = today
                delta = "incremented"
            longest = max(longest, current)
            c.execute(
                "UPDATE user_streaks SET current_count=?, longest_count=?, "
                "last_login_date=?, current_started_at=?, updated_at=datetime('now') "
                "WHERE user_id=?",
                (current, longest, today, started, user_id),
            )
        c.execute(
            "INSERT OR IGNORE INTO login_events (user_id, login_date, source) "
            "VALUES (?,?,?)",
            (user_id, today, source),
        )
    return {"current_count": current, "longest_count": longest,
            "last_login_date": today, "current_started_at": started,
            "delta": delta}


def login_history(user_id: str, from_date: str, to_date: str) -> list[str]:
    with conn() as c:
        rows = c.execute(
            "SELECT login_date FROM login_events "
            "WHERE user_id=? AND login_date BETWEEN ? AND ? "
            "ORDER BY login_date",
            (user_id, from_date, to_date),
        ).fetchall()
    return [r["login_date"] for r in rows]


def list_milestones() -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM streak_milestones ORDER BY threshold_days"
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["reward_payload"] = json.loads(d["reward_payload"])
        out.append(d)
    return out


def user_milestones(user_id: str) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT m.id, m.code, m.threshold_days, m.reward_type, m.reward_payload, "
            "       um.achieved_at "
            "FROM user_milestones um JOIN streak_milestones m ON m.id = um.milestone_id "
            "WHERE um.user_id=? ORDER BY m.threshold_days",
            (user_id,),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["reward_payload"] = json.loads(d["reward_payload"])
        out.append(d)
    return out


def claim_milestone(user_id: str, milestone_id: int) -> bool:
    """Returns True if newly claimed, False if already had it."""
    with conn() as c:
        try:
            c.execute(
                "INSERT INTO user_milestones (user_id, milestone_id) VALUES (?,?)",
                (user_id, milestone_id),
            )
            return True
        except sqlite3.IntegrityError:
            return False


# ──────────────────────────────────────────────────────────────────────────
# Themes / Unlocks / Preferences
# ──────────────────────────────────────────────────────────────────────────
def _theme_row(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["palette"] = json.loads(d["palette"])
    d["unlock_rule"] = json.loads(d["unlock_rule"])
    return d


def list_themes() -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM themes WHERE is_active=1 ORDER BY id"
        ).fetchall()
    return [_theme_row(r) for r in rows]


def get_theme_by_code(code: str) -> dict | None:
    with conn() as c:
        r = c.execute("SELECT * FROM themes WHERE code=?", (code,)).fetchone()
    return _theme_row(r) if r else None


def list_user_unlocks(user_id: str) -> list[int]:
    with conn() as c:
        rows = c.execute(
            "SELECT theme_id FROM user_unlocks WHERE user_id=?", (user_id,)
        ).fetchall()
    return [r["theme_id"] for r in rows]


def unlock_theme(user_id: str, theme_id: int, source: str) -> bool:
    with conn() as c:
        try:
            c.execute(
                "INSERT INTO user_unlocks (user_id, theme_id, source) VALUES (?,?,?)",
                (user_id, theme_id, source),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def get_preferences(user_id: str) -> dict:
    with conn() as c:
        r = c.execute(
            "SELECT p.*, t.code AS active_theme_code "
            "FROM user_preferences p LEFT JOIN themes t ON t.id = p.active_theme_id "
            "WHERE p.user_id=?",
            (user_id,),
        ).fetchone()
        if not r:
            default = c.execute(
                "SELECT id FROM themes WHERE code='default'"
            ).fetchone()
            tid = default["id"] if default else None
            c.execute(
                "INSERT INTO user_preferences (user_id, active_theme_id) VALUES (?,?)",
                (user_id, tid),
            )
            return {"user_id": user_id, "active_theme_id": tid,
                    "active_theme_code": "default" if tid else None,
                    "dashboard_layout": {}, "badge_config": {}}
    return {
        "user_id": r["user_id"],
        "active_theme_id": r["active_theme_id"],
        "active_theme_code": r["active_theme_code"],
        "dashboard_layout": json.loads(r["dashboard_layout"] or "{}"),
        "badge_config": json.loads(r["badge_config"] or "{}"),
    }


def set_active_theme(user_id: str, theme_id: int) -> None:
    get_preferences(user_id)  # ensure row exists
    with conn() as c:
        c.execute(
            "UPDATE user_preferences SET active_theme_id=?, updated_at=datetime('now') "
            "WHERE user_id=?",
            (theme_id, user_id),
        )


def update_preferences(user_id: str, dashboard_layout: dict | None = None,
                       badge_config: dict | None = None,
                       active_theme_id: int | None = None) -> None:
    get_preferences(user_id)
    sets, params = [], []
    if dashboard_layout is not None:
        sets.append("dashboard_layout=?")
        params.append(json.dumps(dashboard_layout))
    if badge_config is not None:
        sets.append("badge_config=?")
        params.append(json.dumps(badge_config))
    if active_theme_id is not None:
        sets.append("active_theme_id=?")
        params.append(active_theme_id)
    if not sets:
        return
    sets.append("updated_at=datetime('now')")
    params.append(user_id)
    with conn() as c:
        c.execute(f"UPDATE user_preferences SET {', '.join(sets)} WHERE user_id=?",
                  params)


# ──────────────────────────────────────────────────────────────────────────
# Activity events
# ──────────────────────────────────────────────────────────────────────────
def log_activity(user_id: str, event_type: str,
                 payload: dict | None = None) -> None:
    with conn() as c:
        c.execute(
            "INSERT INTO activity_events (user_id, event_type, payload) VALUES (?,?,?)",
            (user_id, event_type, json.dumps(payload or {})),
        )


def list_activity(user_id: str, event_type: str | None = None,
                  limit: int = 50, before_id: int | None = None) -> list[dict]:
    """Cursor-paged by descending id."""
    q = "SELECT * FROM activity_events WHERE user_id=?"
    params: list = [user_id]
    if event_type:
        q += " AND event_type=?"
        params.append(event_type)
    if before_id:
        q += " AND id < ?"
        params.append(before_id)
    q += " ORDER BY id DESC LIMIT ?"
    params.append(min(max(limit, 1), 100))
    with conn() as c:
        rows = c.execute(q, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d["payload"] or "{}")
        out.append(d)
    return out


# ──────────────────────────────────────────────────────────────────────────
# Announcements
# ──────────────────────────────────────────────────────────────────────────
def create_announcement(title: str, body: str, tone: str = "info",
                        pinned: bool = False,
                        created_by: str | None = None) -> int:
    with conn() as c:
        cur = c.execute(
            "INSERT INTO announcements (title, body, tone, pinned, created_by) "
            "VALUES (?,?,?,?,?)",
            (title.strip(), body.strip(), tone, 1 if pinned else 0, created_by),
        )
        return cur.lastrowid


def list_active_announcements(limit: int = 5) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM announcements WHERE active=1 "
            "ORDER BY pinned DESC, created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def list_all_announcements(limit: int = 50) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM announcements ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def set_announcement_active(aid: int, active: bool) -> None:
    with conn() as c:
        c.execute("UPDATE announcements SET active=? WHERE id=?",
                  (1 if active else 0, aid))


def delete_announcement(aid: int) -> None:
    with conn() as c:
        c.execute("DELETE FROM announcements WHERE id=?", (aid,))


def set_user_role(user_id: str, role: str) -> None:
    with conn() as c:
        c.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))


# ──────────────────────────────────────────────────────────────────────────
# Class schedule (scraped from PowerSchool)
# ──────────────────────────────────────────────────────────────────────────
def upsert_class(user_id: str | None, *, course: str, teacher: str = "",
                 room: str = "", period: str = "", days: str = "",
                 start_time: str = "", end_time: str = "",
                 source: str = "powerschool", external_id: str = "") -> str:
    """Insert or update a class row. Returns 'added' or 'updated'."""
    if not external_id:
        external_id = f"{source}::{course}::{period}::{days}"
    with conn() as c:
        existing = c.execute(
            "SELECT id FROM class_schedule WHERE user_id IS ? AND external_id=?",
            (user_id, external_id),
        ).fetchone()
        if existing:
            c.execute(
                "UPDATE class_schedule SET course=?, teacher=?, room=?, period=?, "
                "days=?, start_time=?, end_time=?, source=?, "
                "updated_at=datetime('now') WHERE id=?",
                (course, teacher, room, period, days, start_time, end_time,
                 source, existing["id"]),
            )
            return "updated"
        c.execute(
            "INSERT INTO class_schedule "
            "(user_id, course, teacher, room, period, days, start_time, end_time, "
            " source, external_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (user_id, course, teacher, room, period, days, start_time, end_time,
             source, external_id),
        )
        return "added"


def list_classes(user_id: str | None) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM class_schedule WHERE user_id IS ?",
            (user_id,),
        ).fetchall()
    items = [dict(r) for r in rows]

    def _minutes(t: str) -> int:
        if not t:
            return 24 * 60 + 1
        s = t.strip().upper()
        import re
        m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", s)
        if not m:
            return 24 * 60 + 1
        h = int(m.group(1)); mm = int(m.group(2)); ap = m.group(3)
        if ap == "PM" and h != 12: h += 12
        if ap == "AM" and h == 12: h = 0
        return h * 60 + mm

    items.sort(key=lambda r: (_minutes(r.get("start_time") or ""),
                              r.get("period") or "",
                              r.get("course") or ""))
    return items


def clear_classes(user_id: str | None) -> int:
    with conn() as c:
        cur = c.execute("DELETE FROM class_schedule WHERE user_id IS ?", (user_id,))
        return cur.rowcount


# ──────────────────────────────────────────────────────────────────────────
# Lunch ratings
# ──────────────────────────────────────────────────────────────────────────
def add_rating(day: str, stars: int, comment: str = "",
               user_id: str | None = None) -> None:
    with conn() as c:
        c.execute(
            "INSERT INTO lunch_ratings (day, stars, comment, user_id) VALUES (?,?,?,?)",
            (day, stars, comment, user_id),
        )


def ratings_for_day(day: str) -> tuple[float | None, int]:
    with conn() as c:
        row = c.execute(
            "SELECT AVG(stars) AS avg, COUNT(*) AS n FROM lunch_ratings WHERE day=?",
            (day,),
        ).fetchone()
    avg = row["avg"]
    return (float(avg) if avg is not None else None, int(row["n"]))


# ──────────────────────────────────────────────────────────────────────────
# Assignments (scoped by user_id when provided; legacy NULL rows visible to all
# so existing single-user installations keep working).
# ──────────────────────────────────────────────────────────────────────────
def list_assignments(user_id: str | None = None) -> list[dict]:
    with conn() as c:
        if user_id:
            rows = c.execute(
                "SELECT * FROM assignments "
                "WHERE user_id=? OR user_id IS NULL "
                "ORDER BY done ASC, priority ASC, due_at ASC",
                (user_id,),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM assignments "
                "ORDER BY done ASC, priority ASC, due_at ASC"
            ).fetchall()
    return [dict(r) for r in rows]


def add_assignment(title: str, subject: str, due_at: str, priority: int = 99,
                   source: str = "manual", external_id: str | None = None,
                   user_id: str | None = None) -> int:
    with conn() as c:
        cur = c.execute(
            "INSERT INTO assignments "
            "(title, subject, due_at, priority, source, external_id, user_id) "
            "VALUES (?,?,?,?,?,?,?)",
            (title, subject, due_at, priority, source, external_id, user_id),
        )
        return int(cur.lastrowid)


def upsert_external_assignment(title: str, subject: str, due_at: str,
                               source: str, external_id: str,
                               priority: int = 50,
                               user_id: str | None = None) -> str:
    """Returns 'added' or 'updated'."""
    with conn() as c:
        existing = c.execute(
            "SELECT id FROM assignments WHERE source=? AND external_id=?",
            (source, external_id),
        ).fetchone()
        if existing:
            c.execute(
                "UPDATE assignments SET title=?, subject=?, due_at=?, "
                "user_id=COALESCE(user_id, ?), updated_at=datetime('now') "
                "WHERE id=?",
                (title, subject, due_at, user_id, existing["id"]),
            )
            return "updated"
        c.execute(
            "INSERT INTO assignments "
            "(title, subject, due_at, priority, source, external_id, user_id) "
            "VALUES (?,?,?,?,?,?,?)",
            (title, subject, due_at, priority, source, external_id, user_id),
        )
        return "added"


def toggle_assignment(aid: int) -> None:
    with conn() as c:
        c.execute(
            "UPDATE assignments SET done = 1 - done, updated_at=datetime('now') "
            "WHERE id=?",
            (aid,),
        )


def delete_assignment(aid: int) -> None:
    with conn() as c:
        c.execute("DELETE FROM assignments WHERE id=?", (aid,))


def seed_if_empty(demo_assignments: Iterable[dict]) -> None:
    """Seed assignments if the table is empty (first run)."""
    with conn() as c:
        n = c.execute("SELECT COUNT(*) AS n FROM assignments").fetchone()["n"]
    if n == 0:
        for a in demo_assignments:
            add_assignment(a["title"], a["subject"], a["due_at"],
                           a.get("priority", 99))
