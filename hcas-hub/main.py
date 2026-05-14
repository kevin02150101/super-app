"""HCAS Hub — central student super-app.

Run:    uvicorn main:app --reload
Open:   http://127.0.0.1:8000

Set GOOGLE_API_KEY in env for the Notes generator (see README).
Set AZURE_CLIENT_ID + AZURE_TENANT_ID (+ AZURE_CLIENT_SECRET) for Microsoft
OAuth2 login; otherwise the dev login route at /auth/dev/login is used.
"""
import os
import json
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from fastapi import FastAPI, Request, Form, HTTPException, Depends, Body
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
    JSONResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from lib import db, seed, auth, streak as streak_svc, themes as theme_svc
from lib import toolbox as toolbox_lib
from lib.lunch_verdict import verdict_for

BASE = Path(__file__).parent
DATA = BASE / "data"

app = FastAPI(title="HCAS Hub")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

SEED = seed.load()


@app.on_event("startup")
def _startup():
    db.init()
    # seed catalogs (idempotent)
    with open(DATA / "streak_milestones.json") as f:
        db.seed_milestones(json.load(f))
    with open(DATA / "themes.json") as f:
        db.seed_themes(json.load(f))
    # NOTE: demo assignments disabled — uncomment for a fresh empty DB demo.
    # db.seed_if_empty(SEED["demo_assignments"])


# --------- shared template helpers ---------
def _header_ctx(request: Request) -> dict:
    user = auth.current_user(request)
    streak = db.get_streak(user["id"]) if user else None
    prefs = db.get_preferences(user["id"]) if user else None
    return {"user": user, "streak": streak, "prefs": prefs,
            "ms_oauth_on": auth.ms_oauth_configured(),
            "dev_login_on": auth.dev_login_enabled()}


def render(request: Request, template: str, **ctx) -> HTMLResponse:
    ctx.setdefault("school", SEED["school"])
    ctx.setdefault("active", "")
    ctx.update(_header_ctx(request))
    resp = templates.TemplateResponse(request, template, ctx)
    # Always serve fresh HTML so synced HW updates show on reload.
    resp.headers["Cache-Control"] = "no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


# --------- helpers ---------
def _blended_rating(menu: dict, day: str):
    """Combine seeded prior ratings with this app's live ratings (weighted average).

    Returns (avg, total_n, db_n) — db_n is how many ratings came from this app.
    """
    db_avg, db_n = db.ratings_for_day(day)
    prior_avg = menu.get("prior_avg_rating")
    prior_n = menu.get("prior_rating_count", 0) or 0
    total_n = (db_n or 0) + prior_n
    if total_n == 0 or (prior_avg is None and not db_n):
        return None, 0, db_n
    if prior_avg is None:
        return db_avg, db_n, db_n
    avg = ((db_avg or 0) * (db_n or 0) + prior_avg * prior_n) / total_n
    return avg, total_n, db_n


# --------- TODAY ---------
@app.get("/", response_class=HTMLResponse)
def today(request: Request):
    user = auth.current_user(request)
    streak_info = None
    if user:
        streak_info = streak_svc.heartbeat(user["id"], source="web")

    menus = SEED["lunch_menus"]
    day = seed.closest_menu_date(menus)
    menu = menus[day]
    avg, n, _ = _blended_rating(menu, day)
    v = verdict_for(avg, n)

    uid = user["id"] if user else None
    assignments = [a for a in db.list_assignments(uid) if not a["done"]][:4]
    todays_meetings = []
    total_unread = 0
    for team in SEED["teams"]:
        m = team.get("today_meeting")
        if m and seed.is_today(m.get("starts_at")):
            todays_meetings.append({**m, "team": team["name"], "team_url": team["url"]})
        total_unread += team.get("unread", 0)
    todays_meetings.sort(key=lambda m: m["starts_at"])

    return render(
        request,
        "today.html",
        active="today",
        day=day,
        day_label=seed.display_date(day),
        menu=menu,
        verdict=v,
        avg=avg,
        rating_count=n,
        assignments=assignments,
        meetings=todays_meetings,
        unread_total=total_unread,
        now=datetime.now(),
        streak_info=streak_info,
        announcements=db.list_active_announcements(),
    )


# --------- LUNCH ---------
@app.get("/lunch", response_class=HTMLResponse)
def lunch(request: Request, day: str | None = None):
    menus = SEED["lunch_menus"]
    if not day or day not in menus:
        day = seed.closest_menu_date(menus)
    menu = menus[day]
    avg, n, db_n = _blended_rating(menu, day)
    v = verdict_for(avg, n)

    school = SEED["school"]
    uber_url = (
        f"https://www.ubereats.com/feed?diningMode=DELIVERY"
        f"&pl={quote_plus(json.dumps({'address':{'address1': school['address']}}))}"
    )

    week = seed.week_dates(day, menus)
    all_dates = sorted(menus.keys())

    return render(
        request,
        "lunch.html",
        active="lunch",
        day=day,
        day_label=seed.display_date(day),
        week=[(d, seed.short_weekday(d), d.split("-")[-1]) for d in week],
        all_dates=[(d, seed.display_date(d)) for d in all_dates],
        menu=menu,
        verdict=v,
        avg=avg,
        rating_count=n,
        crowd_n=db_n,
        uber_url=uber_url,
        uber_suggestions=_pick_uber_suggestions(),
    )


def _pick_uber_suggestions(n: int = 6) -> list[dict]:
    pool = SEED.get("uber_suggestions") or []
    if len(pool) <= n:
        return list(pool)
    return random.sample(pool, n)


@app.get("/lunch/uber_suggestions.json")
def lunch_uber_suggestions():
    return JSONResponse({"suggestions": _pick_uber_suggestions()})


@app.post("/lunch/rate")
def lunch_rate(request: Request, day: str = Form(...),
               stars: int = Form(...), comment: str = Form("")):
    if day not in SEED["lunch_menus"]:
        raise HTTPException(400, "bad day")
    if stars < 1 or stars > 5:
        raise HTTPException(400, "stars 1-5")
    user = auth.current_user(request)
    uid = user["id"] if user else None
    db.add_rating(day, stars, comment.strip(), user_id=uid)
    if uid:
        db.log_activity(uid, "lunch_rated",
                        {"day": day, "stars": stars})
    return RedirectResponse(f"/lunch?day={day}", status_code=303)


# --------- ASSIGNMENTS ---------
@app.get("/assignments", response_class=HTMLResponse)
def assignments(request: Request):
    user = auth.current_user(request)
    uid = user["id"] if user else None
    rows = db.list_assignments(uid)
    sig = "|".join(f"{r['id']}:{r['done']}:{r['title']}:{r.get('due_at') or ''}" for r in rows)
    return render(request, "assignments.html", active="assignments",
                  assignments=rows, assignments_sig=sig)


@app.get("/api/assignments.json")
def api_assignments_json(request: Request):
    """Lightweight JSON feed used by the assignments page to live-refresh
    after the Chrome extension pushes new rows."""
    user = auth.current_user(request)
    uid = user["id"] if user else None
    return {"assignments": db.list_assignments(uid)}


@app.get("/calendar", response_class=HTMLResponse)
def calendar(request: Request, week_start: str | None = None):
    """Week calendar view of assignments (Mon-Sun)."""
    from datetime import date, timedelta
    today = datetime.now().date()
    if week_start:
        try:
            anchor = datetime.strptime(week_start, "%Y-%m-%d").date()
        except ValueError:
            anchor = today
    else:
        anchor = today
    monday = anchor - timedelta(days=anchor.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    user = auth.current_user(request)
    uid = user["id"] if user else None
    by_day: dict[str, list] = {d.isoformat(): [] for d in days}
    no_due = []
    upcoming = []  # outside the visible week, future
    week_start_d = days[0]
    week_end_d = days[-1]
    for a in db.list_assignments(uid):
        if a["done"]:
            continue
        due = seed.parse_dt(a.get("due_at"))
        if not due:
            no_due.append(a)
            continue
        d = due.date()
        key = d.isoformat()
        if key in by_day:
            by_day[key].append(a)
        elif d > week_end_d:
            upcoming.append(a)

    for k in by_day:
        by_day[k].sort(key=lambda a: a.get("due_at") or "")
    upcoming.sort(key=lambda a: a.get("due_at") or "")

    sig = "|".join(
        f"{a['id']}:{a['done']}:{a['title']}:{a.get('due_at') or ''}"
        for a in db.list_assignments(uid)
    )

    return render(
        request,
        "calendar.html",
        active="assignments",
        days=[(d.isoformat(), d.strftime("%a"), d.strftime("%-d"), d == today) for d in days],
        by_day=by_day,
        no_due=no_due,
        upcoming=upcoming,
        prev_week=(monday - timedelta(days=7)).isoformat(),
        next_week=(monday + timedelta(days=7)).isoformat(),
        this_monday=monday.isoformat(),
        week_label=f"{monday.strftime('%b %-d')} – {(monday+timedelta(days=6)).strftime('%b %-d, %Y')}",
        assignments_sig=sig,
    )


@app.post("/assignments/add")
def assignments_add(
    request: Request,
    title: str = Form(...),
    subject: str = Form(""),
    due_at: str = Form(""),
    priority: int = Form(99),
):
    title = title.strip()
    if not title:
        raise HTTPException(400, "title required")
    user = auth.current_user(request)
    uid = user["id"] if user else None
    aid = db.add_assignment(title, subject.strip(), due_at, priority, user_id=uid)
    if uid:
        db.log_activity(uid, "assignment_added",
                        {"assignment_id": aid, "title": title})
    return RedirectResponse("/assignments", status_code=303)


@app.post("/assignments/{aid}/toggle")
def assignments_toggle(request: Request, aid: int):
    db.toggle_assignment(aid)
    user = auth.current_user(request)
    if user:
        db.log_activity(user["id"], "assignment_toggled", {"assignment_id": aid})
    return RedirectResponse("/assignments", status_code=303)


@app.post("/assignments/{aid}/delete")
def assignments_delete(request: Request, aid: int):
    db.delete_assignment(aid)
    user = auth.current_user(request)
    if user:
        db.log_activity(user["id"], "assignment_deleted", {"assignment_id": aid})
    return RedirectResponse("/assignments", status_code=303)


# --------- IMPORT FROM CHROME EXTENSION (Microsoft Teams) ---------
# CORS preflight (Chrome extension fetches require Access-Control-Allow-Origin
# even when the request goes to localhost).
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # safe for local-only dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/import_assignments")
async def api_import_assignments(request: Request):
    body = await request.json()
    rows = body.get("rows", [])
    user = auth.current_user(request)
    # Synced assignments are install-wide (visible to anyone on this Hub).
    # The extension's fetch may or may not carry the user's session cookie,
    # so scoping by uid causes synced HW to vanish for other tabs/accounts.
    uid = None
    added = updated = skipped = 0
    for r in rows:
        title = (r.get("title") or "").strip()[:200]
        if not title:
            skipped += 1
            continue
        subject = (r.get("subject") or "").strip()[:80]
        due_at = (r.get("due_at") or "").strip()[:32]
        ext_id = (r.get("external_id") or "").strip()[:200]
        source = (r.get("source") or "teams").strip()[:32]
        if not ext_id:
            ext_id = f"{source}::{title}::{subject}::{due_at}"
        outcome = db.upsert_external_assignment(
            title=title, subject=subject, due_at=due_at,
            source=source, external_id=ext_id, priority=50,
            user_id=uid,
        )
        if outcome == "added":
            added += 1
        else:
            updated += 1
    if uid:
        db.log_activity(uid, "schedule_synced",
                        {"added": added, "updated": updated, "skipped": skipped,
                         "source": "extension"})
    return {"ok": True, "added": added, "updated": updated, "skipped": skipped}


@app.post("/api/import_schedule")
async def api_import_schedule(request: Request):
    """Import a class/period schedule scraped from PowerSchool."""
    body = await request.json()
    rows = body.get("rows", [])
    replace = bool(body.get("replace"))
    user = auth.current_user(request)
    uid = user["id"] if user else None
    if replace:
        db.clear_classes(uid)
    added = updated = skipped = 0
    for r in rows:
        course = (r.get("course") or r.get("title") or "").strip()[:120]
        if not course:
            skipped += 1
            continue
        outcome = db.upsert_class(
            uid,
            course=course,
            teacher=(r.get("teacher") or "").strip()[:80],
            room=(r.get("room") or "").strip()[:40],
            period=(r.get("period") or "").strip()[:20],
            days=(r.get("days") or "").strip()[:20],
            start_time=(r.get("start_time") or "").strip()[:16],
            end_time=(r.get("end_time") or "").strip()[:16],
            source=(r.get("source") or "powerschool").strip()[:32],
            external_id=(r.get("external_id") or "").strip()[:200],
        )
        if outcome == "added":
            added += 1
        else:
            updated += 1
    if uid:
        db.log_activity(uid, "schedule_synced",
                        {"added": added, "updated": updated, "skipped": skipped,
                         "kind": "classes", "source": "powerschool"})
    return {"ok": True, "added": added, "updated": updated, "skipped": skipped}


@app.get("/schedule", response_class=HTMLResponse)
def schedule_page(request: Request):
    user = auth.current_user(request)
    uid = user["id"] if user else None
    classes = db.list_classes(uid)
    # Build current week's Monday..Friday dates for the header.
    from datetime import date as _date, timedelta as _td
    today = _date.today()
    monday = today - _td(days=today.weekday())
    week_dates = [(monday + _td(days=i)).strftime("%m/%d/%Y") for i in range(5)]
    return render(request, "schedule.html", active="",
                  classes=classes, week_dates=week_dates)


@app.post("/schedule/clear")
def schedule_clear(request: Request):
    user = auth.require_user(request)
    db.clear_classes(user["id"])
    return RedirectResponse("/schedule", status_code=303)


# --------- TOOLBOX (external app launcher) ---------
@app.get("/toolbox", response_class=HTMLResponse)
def toolbox(request: Request):
    tools = []
    for t in toolbox_lib.TOOLS.values():
        tools.append(
            {
                "key": t.key,
                "name": t.name,
                "tagline": t.tagline,
                "description": t.description,
                "stack": t.stack,
                "badge": t.badge,
                "url": t.url,
                "port": t.port,
                "running": toolbox_lib.is_running(t.port),
            }
        )
    return render(request, "toolbox.html", active="toolbox", tools=tools)


@app.get("/toolbox/status")
def toolbox_status():
    return JSONResponse(
        {"tools": [toolbox_lib.status(t) for t in toolbox_lib.TOOLS.values()]}
    )


@app.post("/toolbox/launch/{key}")
def toolbox_launch(key: str):
    tool = toolbox_lib.TOOLS.get(key)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {key}")
    return JSONResponse(toolbox_lib.launch(tool))


# --------- NOTES ---------
@app.get("/notes", response_class=HTMLResponse)
def notes(request: Request):
    has_key = bool(os.environ.get("GOOGLE_API_KEY"))
    return render(request, "notes.html", active="notes", has_key=has_key)


@app.post("/notes/generate")
def notes_generate(topic: str = Form(...)):
    topic = topic.strip()
    if not topic:
        raise HTTPException(400, "topic required")
    if not os.environ.get("GOOGLE_API_KEY"):
        # Friendly fallback so the demo never hard-fails
        def _missing():
            yield (
                f"# {topic}\n\n"
                "**Notes generator needs an API key.**\n\n"
                "Set `GOOGLE_API_KEY` in your environment, then restart the server. "
                "See the README for instructions.\n"
            )
        return StreamingResponse(_missing(), media_type="text/plain")

    # Lazy import so the server still boots without the key set
    from lib.claude import stream_notes

    def gen():
        try:
            for chunk in stream_notes(topic):
                yield chunk
        except Exception as e:
            yield f"\n\n**Error:** {e}\n"

    return StreamingResponse(gen(), media_type="text/plain")


# --------- PWA ---------
@app.get("/manifest.webmanifest")
def manifest():
    return JSONResponse(
        {
            "name": "HCAS Hub",
            "short_name": "HCAS Hub",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0f172a",
            "theme_color": "#0f172a",
            "icons": [
                {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"},
            ],
        },
        media_type="application/manifest+json",
    )


# ═══════════════════════════════════════════════════════════════════════
# AUTH  (PRD §4.1 / §6.2)
# ═══════════════════════════════════════════════════════════════════════
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render(request, "login.html", active="")


@app.get("/auth/dev/login")
def auth_dev_login(request: Request, email: str, name: str = "", password: str = ""):
    if not auth.dev_login_enabled():
        raise HTTPException(403, "dev login disabled")
    user = auth.dev_login(email, name, password)
    resp = RedirectResponse("/", status_code=303)
    auth.issue_session_cookie(resp, user["id"], request)
    streak_svc.heartbeat(user["id"], source="dev")
    db.log_activity(user["id"], "login", {"via": "dev"})
    return resp


@app.post("/auth/dev/login")
def auth_dev_login_post(
    request: Request,
    email: str = Form(...),
    name: str = Form(""),
    password: str = Form(""),
):
    if not auth.dev_login_enabled():
        raise HTTPException(403, "dev login disabled")
    user = auth.dev_login(email, name, password)
    resp = RedirectResponse("/", status_code=303)
    auth.issue_session_cookie(resp, user["id"], request)
    streak_svc.heartbeat(user["id"], source="dev")
    db.log_activity(user["id"], "login", {"via": "dev"})
    return resp


@app.get("/auth/microsoft/login")
def auth_ms_login(request: Request):
    redirect_uri = str(request.url_for("auth_ms_callback"))
    return RedirectResponse(auth.ms_build_auth_url(redirect_uri), status_code=303)


@app.get("/auth/microsoft/callback", name="auth_ms_callback")
def auth_ms_callback(request: Request, code: str, state: str):
    redirect_uri = str(request.url_for("auth_ms_callback"))
    user = auth.ms_handle_callback(code, state, redirect_uri)
    resp = RedirectResponse("/me", status_code=303)
    auth.issue_session_cookie(resp, user["id"], request)
    streak_svc.heartbeat(user["id"], source="microsoft")
    db.log_activity(user["id"], "login", {"via": "microsoft"})
    return resp


@app.post("/auth/logout")
def auth_logout(request: Request):
    resp = RedirectResponse("/login", status_code=303)
    auth.clear_session_cookie(resp, request)
    return resp


# ═══════════════════════════════════════════════════════════════════════
# /me  —  profile + streak + themes + history
# ═══════════════════════════════════════════════════════════════════════
@app.get("/me", response_class=HTMLResponse)
def me_page(request: Request, user=Depends(auth.require_user)):
    streak = db.get_streak(user["id"])
    history = streak_svc.streak_history(user["id"], days=30)
    achieved = db.user_milestones(user["id"])
    achieved_codes = {m["code"] for m in achieved}
    all_ms = db.list_milestones()
    milestone_view = [
        {**m, "achieved": m["code"] in achieved_codes,
         "progress": min(100, int(streak["current_count"] * 100 / m["threshold_days"]))}
        for m in all_ms
    ]
    themes = theme_svc.list_for_user(user["id"])
    recent = db.list_activity(user["id"], limit=20)
    return render(
        request, "profile.html", active="me",
        streak=streak, history=history,
        milestones=milestone_view,
        themes=themes, recent=recent,
    )


# ─── JSON API ────────────────────────────────────────────────────────────
@app.get("/api/v1/me")
def api_me(user=Depends(auth.require_user)):
    return {"id": user["id"], "email": user["email"],
            "display_name": user["display_name"],
            "avatar_url": user["avatar_url"], "role": user["role"]}


@app.delete("/api/v1/me/account")
def api_delete_account(request: Request, user=Depends(auth.require_user)):
    db.soft_delete_user(user["id"])
    db.log_activity(user["id"], "account_deleted", {})
    resp = JSONResponse({"ok": True})
    auth.clear_session_cookie(resp, request)
    return resp


@app.get("/api/v1/me/streak")
def api_streak(user=Depends(auth.require_user)):
    return {**db.get_streak(user["id"]),
            "milestones": db.user_milestones(user["id"])}


@app.post("/api/v1/me/streak/heartbeat")
def api_streak_heartbeat(user=Depends(auth.require_user)):
    return streak_svc.heartbeat(user["id"], source="api")


@app.get("/api/v1/me/streak/history")
def api_streak_history(days: int = 30, user=Depends(auth.require_user)):
    days = max(1, min(days, 365))
    return {"data": streak_svc.streak_history(user["id"], days=days)}


@app.get("/api/v1/me/themes")
def api_themes(user=Depends(auth.require_user)):
    return {"data": theme_svc.list_for_user(user["id"])}


@app.post("/api/v1/me/themes/activate")
def api_activate_theme(payload: dict = Body(...),
                       user=Depends(auth.require_user)):
    code = (payload or {}).get("theme_code", "").strip()
    if not code:
        raise HTTPException(400, "theme_code required")
    theme = theme_svc.activate(user["id"], code)
    return {"ok": True, "theme": {"code": theme["code"], "palette": theme["palette"]}}


@app.get("/api/v1/me/preferences")
def api_get_prefs(user=Depends(auth.require_user)):
    return db.get_preferences(user["id"])


@app.put("/api/v1/me/preferences")
def api_put_prefs(payload: dict = Body(...),
                  user=Depends(auth.require_user)):
    db.update_preferences(
        user["id"],
        dashboard_layout=payload.get("dashboard_layout"),
        badge_config=payload.get("badge_config"),
    )
    return db.get_preferences(user["id"])


@app.get("/api/v1/me/history")
def api_history(event_type: str | None = None,
                limit: int = 20,
                before_id: int | None = None,
                user=Depends(auth.require_user)):
    rows = db.list_activity(user["id"], event_type=event_type,
                            limit=limit, before_id=before_id)
    next_cursor = rows[-1]["id"] if len(rows) == limit else None
    return {"data": rows, "next_cursor": next_cursor}


# Form-submit variant of theme activate (works without JS)
@app.post("/me/themes/activate")
def me_activate_theme_form(request: Request, theme_code: str = Form(...),
                           user=Depends(auth.require_user)):
    theme_svc.activate(user["id"], theme_code)
    return RedirectResponse("/me", status_code=303)


# ═══════════════════════════════════════════════════════════════════════
# Admin  (PRD §6.2)
# ═══════════════════════════════════════════════════════════════════════
@app.get("/api/v1/admin/metrics")
def admin_metrics(user=Depends(auth.require_admin)):
    with db.conn() as c:
        users_total = c.execute(
            "SELECT COUNT(*) AS n FROM users WHERE deleted_at IS NULL"
        ).fetchone()["n"]
        active_streaks = c.execute(
            "SELECT COUNT(*) AS n FROM user_streaks WHERE current_count > 0"
        ).fetchone()["n"]
        recent_logins = c.execute(
            "SELECT COUNT(DISTINCT user_id) AS n FROM login_events "
            "WHERE login_date >= date('now','-7 day')"
        ).fetchone()["n"]
    return {"users_total": users_total,
            "active_streaks": active_streaks,
            "wau": recent_logins}


@app.post("/api/v1/admin/streak/{user_id}/reset")
def admin_reset_streak(user_id: str, admin=Depends(auth.require_admin)):
    with db.conn() as c:
        c.execute(
            "UPDATE user_streaks SET current_count=0, current_started_at=NULL, "
            "updated_at=datetime('now') WHERE user_id=?",
            (user_id,),
        )
    db.log_activity(admin["id"], "admin_reset_streak", {"target_user": user_id})
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════
# Announcements — admin posts, everyone sees on the home page
# ═══════════════════════════════════════════════════════════════════════
@app.get("/admin", response_class=HTMLResponse)
def admin_console(request: Request, admin=Depends(auth.require_admin)):
    return render(
        request, "admin.html", active="admin",
        announcements=db.list_all_announcements(),
    )


@app.post("/admin/announcements/new")
def admin_announce_new(request: Request,
                       title: str = Form(...),
                       body: str = Form(""),
                       tone: str = Form("info"),
                       pinned: str = Form(""),
                       admin=Depends(auth.require_admin)):
    title = title.strip()
    if not title:
        raise HTTPException(400, "title required")
    if tone not in {"info", "warn", "success"}:
        tone = "info"
    aid = db.create_announcement(
        title=title, body=body, tone=tone,
        pinned=bool(pinned), created_by=admin["id"],
    )
    db.log_activity(admin["id"], "announcement_posted",
                    {"id": aid, "title": title})
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/announcements/{aid}/toggle")
def admin_announce_toggle(aid: int, admin=Depends(auth.require_admin)):
    with db.conn() as c:
        row = c.execute("SELECT active FROM announcements WHERE id=?",
                        (aid,)).fetchone()
        if not row:
            raise HTTPException(404, "not found")
    db.set_announcement_active(aid, not bool(row["active"]))
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/announcements/{aid}/delete")
def admin_announce_delete(aid: int, admin=Depends(auth.require_admin)):
    db.delete_announcement(aid)
    return RedirectResponse("/admin", status_code=303)


@app.get("/api/v1/announcements")
def api_announcements():
    """Public list of active announcements (shown on home page)."""
    return {"data": db.list_active_announcements()}
