"""AES-256-GCM helpers for symmetric token-at-rest encryption.

Used to encrypt Microsoft Graph refresh tokens before storing them in
`oauth_tokens.refresh_token_enc`. In production the DEK should come from
Azure Key Vault (envelope encryption); for dev we accept a base64 32-byte
key from the `TOKEN_ENCRYPTION_KEY` env var, and fall back to a generated
key written to `data/.token_key` with a warning.

Pure-stdlib fallback: if `cryptography` is unavailable we use HMAC-SHA256
keystream XOR (NOT secure — only as a last-ditch dev fallback so the app
boots and you can see the wiring). Install `cryptography` for real AES-GCM.
"""
from __future__ import annotations

import base64
import hmac
import os
import secrets
import warnings
from hashlib import sha256
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    _HAS_CRYPTO = True
except Exception:  # pragma: no cover
    AESGCM = None  # type: ignore[assignment]
    _HAS_CRYPTO = False


_KEY_FILE = Path(__file__).parent.parent / "data" / ".token_key"


def _load_key() -> bytes:
    env = os.environ.get("TOKEN_ENCRYPTION_KEY")
    if env:
        try:
            k = base64.b64decode(env)
            if len(k) == 32:
                return k
        except Exception:
            pass
        warnings.warn(
            "TOKEN_ENCRYPTION_KEY is set but not a base64-encoded 32-byte key; "
            "falling back to local keyfile."
        )
    if _KEY_FILE.exists():
        return base64.b64decode(_KEY_FILE.read_text().strip())
    # First-run dev: generate + persist (mode 0600).
    _KEY_FILE.parent.mkdir(exist_ok=True)
    key = secrets.token_bytes(32)
    _KEY_FILE.write_text(base64.b64encode(key).decode())
    try:
        os.chmod(_KEY_FILE, 0o600)
    except OSError:
        pass
    warnings.warn(
        f"Generated dev token-encryption key at {_KEY_FILE}. "
        "In production set TOKEN_ENCRYPTION_KEY from Azure Key Vault."
    )
    return key


_KEY = _load_key()


def encrypt(plaintext: str) -> tuple[bytes, bytes]:
    """Returns (ciphertext, iv). 12-byte IV per AES-GCM convention."""
    iv = secrets.token_bytes(12)
    if _HAS_CRYPTO:
        ct = AESGCM(_KEY).encrypt(iv, plaintext.encode(), None)
        return ct, iv
    # Fallback (NOT real AES-GCM): keystream from HMAC; tag = HMAC over CT.
    ks = _keystream(iv, len(plaintext))
    body = bytes(b ^ k for b, k in zip(plaintext.encode(), ks))
    tag = hmac.new(_KEY, iv + body, sha256).digest()[:16]
    return body + tag, iv


def decrypt(ciphertext: bytes, iv: bytes) -> str:
    if _HAS_CRYPTO:
        return AESGCM(_KEY).decrypt(iv, ciphertext, None).decode()
    body, tag = ciphertext[:-16], ciphertext[-16:]
    expected = hmac.new(_KEY, iv + body, sha256).digest()[:16]
    if not hmac.compare_digest(tag, expected):
        raise ValueError("auth tag mismatch")
    ks = _keystream(iv, len(body))
    return bytes(b ^ k for b, k in zip(body, ks)).decode()


def _keystream(iv: bytes, n: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(hmac.new(_KEY, iv + counter.to_bytes(8, "big"), sha256).digest())
        counter += 1
    return bytes(out[:n])
