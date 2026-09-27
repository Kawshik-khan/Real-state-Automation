"""Security utilities: password hashing and JWT access/refresh token handling.

Token model
-----------
* Every login creates a session id (``sid``) shared by the access token and the
  refresh-token chain rotated from it.
* Access tokens (``type=access``, 15 min) are the only tokens accepted on protected
  routes. Refresh tokens (``type=refresh``, 7 days) are only accepted by ``/auth/refresh``.
  Stream tickets (``type=stream``, 60 s) are only accepted by EventSource/WebSocket routes.
* Revocation state lives in ``token_store`` (memory -> Redis -> PostgreSQL), so logout,
  rotation and replay detection hold across workers and restarts:
    - refresh ``jti`` active/revoked records (rotation, logout, replay detection)
    - revoked sessions (logout / replay kill the session, including its access tokens)
    - per-user cut-off (tokens issued before it are invalid, e.g. after a password reset)
"""

import hashlib
import hmac
import time
import uuid
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt

from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "access_token_expire_minutes", 15)
REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, "refresh_token_expire_days", 7)
MIN_JWT_SECRET_LENGTH = 32

def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# JWT signing keys that were published in this repository as config defaults.
_PUBLIC_JWT_SECRET_SHA256 = frozenset({
    _sha256("glg_assets_default_jwt_secret_key_2026_minimum_32_chars"),
})


def _load_signing_key() -> str:
    """JWT signing key must be its own private secret — never a published default and
    never the automation/service secret."""
    key = (settings.jwt_secret or "").strip()
    if len(key) < MIN_JWT_SECRET_LENGTH:
        raise RuntimeError(
            f"JWT_SECRET must be set to a random value of at least {MIN_JWT_SECRET_LENGTH} characters "
            "(e.g. `openssl rand -hex 32`)."
        )
    if _sha256(key) in _PUBLIC_JWT_SECRET_SHA256:
        raise RuntimeError("JWT_SECRET is a publicly known default value; set a private random value.")
    if settings.automation_shared_secret and hmac.compare_digest(key, settings.automation_shared_secret):
        raise RuntimeError("JWT_SECRET must differ from AUTOMATION_SHARED_SECRET.")
    return key


SECRET_KEY = _load_signing_key()


# ── Password hashing ─────────────────────────────────────────────────────────

_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def _bcrypt_input(password: str) -> bytes:
    # bcrypt reads at most 72 bytes; truncate exactly like passlib so hashes stored by earlier
    # releases (passlib bcrypt) keep verifying.
    return password.encode("utf-8")[:72]


def _hash_password_legacy(password: str) -> str:
    """Legacy HMAC-SHA256 hasher — used only to verify pre-bcrypt hashes during migration."""
    salt = settings.password_hash_salt
    return hmac.new(salt.encode("utf-8"), password.encode("utf-8"), hashlib.sha256).hexdigest()


_legacy_hash = _hash_password_legacy


def hash_password(password: str) -> str:
    """Hash a password with bcrypt (per-hash random salt, cost 12)."""
    return bcrypt.hashpw(_bcrypt_input(password), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time verification of bcrypt hashes and legacy HMAC hashes."""
    if not hashed_password or plain_password is None:
        return False
    if hashed_password.startswith(_BCRYPT_PREFIXES):
        try:
            return bcrypt.checkpw(_bcrypt_input(plain_password), hashed_password.encode("ascii"))
        except ValueError:
            return False
    return hmac.compare_digest(_hash_password_legacy(plain_password), hashed_password)


def password_needs_rehash(hashed_password: str) -> bool:
    """True for legacy (pre-bcrypt) hashes that should be upgraded on next login."""
    return not (hashed_password or "").startswith(_BCRYPT_PREFIXES)


# ── JWT creation / decoding ──────────────────────────────────────────────────

def _encode(payload: Dict[str, Any]) -> str:
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode(token: str, expected_type: str) -> Optional[Dict[str, Any]]:
    """Verify signature + expiry and require the expected token ``type``."""
    if not token or not isinstance(token, str) or not token.strip():
        return None
    try:
        payload = jwt.decode(
            token.strip(),
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError:
        return None
    if payload.get("type") != expected_type or not payload.get("sid"):
        return None
    return payload


def create_access_token(data: Dict[str, Any], expires_delta_minutes: Optional[int] = None) -> str:
    """Create a short-lived access token (default 15 minutes)."""
    now = int(time.time())
    payload = {k: v for k, v in data.items() if k not in ("type", "exp", "iat", "jti")}
    payload.setdefault("sid", str(uuid.uuid4()))
    minutes = ACCESS_TOKEN_EXPIRE_MINUTES if expires_delta_minutes is None else expires_delta_minutes
    payload.update({
        "iat": now,
        "exp": now + minutes * 60,
        "jti": str(uuid.uuid4()),
        "type": "access",
    })
    return _encode(payload)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Stateless check (signature, expiry, type=access). Does NOT consult revocation state;
    use ``validate_access_token`` for authorization decisions."""
    return _decode(token, "access")


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    return _decode(token, "refresh")


async def _is_revoked(payload: Dict[str, Any]) -> bool:
    from app.core.token_store import token_store

    if await token_store.is_session_revoked(payload["sid"]):
        return True
    cutoff = await token_store.get_user_revoked_cutoff(payload["sub"])
    return cutoff is not None and int(payload.get("iat", 0)) <= cutoff


async def validate_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Full access-token check including logout / replay revocation."""
    payload = decode_access_token(token)
    if not payload or await _is_revoked(payload):
        return None
    return payload


STREAM_TICKET_TTL_SECONDS = 60


def create_stream_ticket(user: Dict[str, Any]) -> str:
    """Short-lived token for EventSource/WebSocket URLs, which cannot carry an
    Authorization header. Scoped (type=stream) so it is useless on normal API routes, and
    brief so a copy leaked into a proxy log expires almost immediately."""
    now = int(time.time())
    return _encode({
        "sub": user["sub"],
        "email": user.get("email"),
        "role": user.get("role"),
        "tenant_id": user.get("tenant_id") or settings.default_tenant_id,
        "sid": user["sid"],
        "type": "stream",
        "iat": now,
        "exp": now + STREAM_TICKET_TTL_SECONDS,
        "jti": str(uuid.uuid4()),
    })


async def validate_stream_ticket(token: str) -> Optional[Dict[str, Any]]:
    payload = _decode(token, "stream")
    if not payload or await _is_revoked(payload):
        return None
    return payload


async def create_refresh_token(data: Dict[str, Any], expires_delta_days: Optional[int] = None) -> str:
    """Create a refresh token bound to the session ``sid`` and register it as active."""
    from app.core.token_store import token_store

    now = int(time.time())
    lifetime = (expires_delta_days or REFRESH_TOKEN_EXPIRE_DAYS) * 86400
    jti = str(uuid.uuid4())
    payload = {
        "sub": data.get("sub", "unknown"),
        "email": data.get("email", ""),
        "role": data.get("role", "agent"),
        "tenant_id": data.get("tenant_id") or settings.default_tenant_id,
        "sid": data.get("sid") or str(uuid.uuid4()),
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": now + lifetime,
    }
    await token_store.record_active_token(
        jti=jti,
        user_id=payload["sub"],
        role=payload["role"],
        email=payload["email"],
        expires_at=payload["exp"],
    )
    return _encode(payload)


async def revoke_session(sid: str, user_id: str = "unknown", reason: str = "logout") -> None:
    from app.core.token_store import token_store

    await token_store.revoke_session(sid, user_id=user_id, ttl_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
                                     reason=reason)


async def verify_and_rotate_refresh_token(
    old_token: str,
) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict[str, Any]], str]:
    """Refresh Token Rotation (RTR) with replay detection.

    Returns (is_valid, new_access_token, new_refresh_token, user_payload, message).
    """
    from app.core.token_store import token_store

    payload = decode_refresh_token(old_token)
    if not payload or not payload.get("jti"):
        return False, None, None, None, "Invalid or expired refresh token."
    if await _is_revoked(payload):
        return False, None, None, None, "Session has been revoked."

    jti, sub, sid = payload["jti"], payload["sub"], payload["sid"]

    # Replay: a rotated/revoked token presented again => kill the session family and every
    # other session of this user.
    if await token_store.is_token_revoked(jti, user_id=sub, issued_at=payload.get("iat")):
        await revoke_session(sid, user_id=sub, reason="replay_attack")
        await token_store.revoke_all_user_tokens(sub, reason="replay_attack")
        return False, None, None, None, "Security breach: Replayed refresh token detected. All sessions revoked."

    if await token_store.get_active_token(jti) is None:
        return False, None, None, None, "Refresh token expired or unrecognized."

    await token_store.revoke_token(jti, sub, float(payload["exp"]), reason="rotation")

    user_data = {
        "sub": sub,
        "email": payload.get("email", ""),
        "role": payload.get("role", "agent"),
        "tenant_id": payload.get("tenant_id") or settings.default_tenant_id,
        "sid": sid,
    }
    new_access_token = create_access_token(user_data)
    new_refresh_token = await create_refresh_token(user_data)
    return True, new_access_token, new_refresh_token, user_data, "Token rotated successfully."


async def revoke_refresh_token(token: str) -> bool:
    """Logout: revoke the refresh token and its session (which also kills its access tokens)."""
    from app.core.token_store import token_store

    payload = decode_refresh_token(token)
    if not payload or not payload.get("jti"):
        return False
    await token_store.revoke_token(payload["jti"], payload["sub"], float(payload["exp"]), reason="logout")
    await revoke_session(payload["sid"], user_id=payload["sub"], reason="logout")
    return True


async def revoke_all_user_tokens(user_id: str) -> int:
    """Invalidate every token issued to a user so far (e.g. password change, compromise)."""
    from app.core.token_store import token_store

    return await token_store.revoke_all_user_tokens(user_id, reason="admin_or_security")
