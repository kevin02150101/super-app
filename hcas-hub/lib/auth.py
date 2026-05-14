"""Authentication for HCAS Hub.

Two login paths share the same session machinery:

  • Microsoft OAuth2 (production) — Authorization Code + PKCE via `msal`.
    Activated when `AZURE_CLIENT_ID` + `AZURE_TENANT_ID` are set.
    Refresh tokens are encrypted with `lib.crypto_util` before being stored.

  • Dev login — `/auth/dev/login?email=...&name=...` creates/finds a user
    and issues a session immediately. Disabled in production by setting
    `HCAS_DISABLE_DEV_LOGIN=1`.

The session is an opaque random token in an `HttpOnly`, `SameSite=Lax`
cookie. Only its SHA-256 hash is stored in DB.
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime
from typing import Optional

from fastapi import Request, HTTPException, status

from . import db, crypto_util

COOKIE_NAME = "hcas_session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

MS_SCOPES = [
    "openid",
    "profile",
    "email",
    "offline_access",
    "User.Read",
    "Calendars.Read",
    # "EduAssignments.ReadBasic",  # add when school IT approves
]


# ──────────────────────────────────────────────────────────────────────────
# Current-user dependency
# ──────────────────────────────────────────────────────────────────────────
def current_user(request: Request) -> Optional[dict]:
    """Resolve the session cookie to a user row (or None)."""
    token = request.cookies.get(COOKIE_NAME)
    return db.session_user(token)


def require_user(request: Request) -> dict:
    user = current_user(request)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "login required")
    return user


def require_admin(request: Request) -> dict:
    user = require_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")
    return user


# ──────────────────────────────────────────────────────────────────────────
# Session issuance / revocation
# ──────────────────────────────────────────────────────────────────────────
def issue_session_cookie(response, user_id: str, request: Request) -> str:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")[:200]
    token = db.create_session(user_id, ip=ip, user_agent=ua)
    response.set_cookie(
        COOKIE_NAME, token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=os.environ.get("HCAS_SECURE_COOKIES") == "1",
        path="/",
    )
    return token


def clear_session_cookie(response, request: Request) -> None:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        db.revoke_session(token)
    response.delete_cookie(COOKIE_NAME, path="/")


# ──────────────────────────────────────────────────────────────────────────
# Dev login
# ──────────────────────────────────────────────────────────────────────────
def dev_login_enabled() -> bool:
    return os.environ.get("HCAS_DISABLE_DEV_LOGIN") != "1"


def dev_login(email: str, display_name: str, password: str = "") -> dict:
    """Create-or-find a user by email and return the user row.

    If the email appears in HCAS_ADMIN_EMAILS (comma-separated), the supplied
    password must match HCAS_ADMIN_PASSWORD (default 'admin@123'); the user is
    then upserted with role='admin'. Non-admin emails do not require a password.
    """
    email = email.strip().lower()
    name = (display_name or email.split("@")[0]).strip() or "Student"
    admin_emails = {e.strip().lower() for e in
                    os.environ.get("HCAS_ADMIN_EMAILS", "").split(",") if e.strip()}
    admin_password = os.environ.get("HCAS_ADMIN_PASSWORD", "admin@123")
    if email in admin_emails:
        if password != admin_password:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "bad admin password")
        role = "admin"
    else:
        role = "student"
    user = db.upsert_user(email=email, display_name=name, role=role)
    # If user existed previously as student but is now in the admin list, promote.
    if role == "admin" and user.get("role") != "admin":
        db.set_user_role(user["id"], "admin")
        user["role"] = "admin"
    return user


# ──────────────────────────────────────────────────────────────────────────
# Microsoft OAuth2 (Authorization Code + PKCE)
# ──────────────────────────────────────────────────────────────────────────
def ms_oauth_configured() -> bool:
    return bool(os.environ.get("AZURE_CLIENT_ID")
                and os.environ.get("AZURE_TENANT_ID"))


def _msal_app():
    import msal  # imported lazily so the app boots without it installed
    return msal.ConfidentialClientApplication(
        client_id=os.environ["AZURE_CLIENT_ID"],
        client_credential=os.environ.get("AZURE_CLIENT_SECRET"),
        authority=f"https://login.microsoftonline.com/{os.environ['AZURE_TENANT_ID']}",
    )


# In-memory state store for OAuth `state` values. Production should use Redis.
_STATE_STORE: dict[str, dict] = {}


def ms_build_auth_url(redirect_uri: str) -> str:
    if not ms_oauth_configured():
        raise HTTPException(501, "Microsoft OAuth not configured")
    app = _msal_app()
    state = secrets.token_urlsafe(24)
    _STATE_STORE[state] = {"created_at": datetime.utcnow().isoformat()}
    return app.get_authorization_request_url(
        scopes=[s for s in MS_SCOPES if s not in {"openid", "profile", "email", "offline_access"}],
        state=state,
        redirect_uri=redirect_uri,
    )


def ms_handle_callback(code: str, state: str, redirect_uri: str) -> dict:
    if state not in _STATE_STORE:
        raise HTTPException(400, "bad state")
    _STATE_STORE.pop(state, None)
    app = _msal_app()
    result = app.acquire_token_by_authorization_code(
        code,
        scopes=[s for s in MS_SCOPES if s not in {"openid", "profile", "email", "offline_access"}],
        redirect_uri=redirect_uri,
    )
    if "access_token" not in result:
        raise HTTPException(400, f"oauth failed: {result.get('error_description', '?')}")

    claims = result.get("id_token_claims") or {}
    ms_oid = claims.get("oid") or claims.get("sub")
    email = claims.get("preferred_username") or claims.get("email") or ""
    name = claims.get("name") or email.split("@")[0]
    user = db.upsert_user(email=email.lower(), display_name=name, ms_oid=ms_oid)

    refresh = result.get("refresh_token")
    if refresh:
        ct, iv = crypto_util.encrypt(refresh)
        expires_at = datetime.utcnow().isoformat()  # access expiry — refresh has no inherent lifetime in MSAL response
        db.save_oauth_token(user["id"], ct, iv,
                            scopes=result.get("scope", "").split(),
                            expires_at_iso=expires_at)
    return user


def get_refresh_token(user_id: str) -> Optional[str]:
    row = db.get_oauth_token(user_id)
    if not row:
        return None
    return crypto_util.decrypt(row["refresh_token_enc"], row["refresh_token_iv"])
