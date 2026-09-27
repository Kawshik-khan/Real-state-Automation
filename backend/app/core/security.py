"""Security utilities: password hashing and JWT access/refresh token handling.

Token model
-----------
* Every login creates a session id (``sid``) shared by the access token and the
  refresh-token chain rotated from it.
* Access tokens (``type=access``, 15 min) are the only tokens accepted on protected
  routes. Refresh tokens (``type=refresh``, 7 days) are only accepted by ``/auth/refresh``.
* Revocation state lives in ``resilient_store`` (Redis when ``REDIS_URL`` is set, else
  per-process memory) so logout / replay detection is shared across workers:
    - ``auth:session_revoked:{sid}``   logout or replay kills the session (access + refresh)
    - ``auth:refresh_active:{jti}``    refresh token issued and not yet rotated
    - ``auth:refresh_used:{jti}``      rotated refresh token (re-use => replay attack)
    - ``auth:user_revoked_before:{sub}`` tokens issued before this epoch are invalid
"""

import base64
import hashlib
import hmac
import time
import uuid
from typing import Any, Dict, Optional, Tuple

import bcrypt
import jwt

from app.config import settings
from app.core.redis_client import resilient_store

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "access_token_expire_minutes", 15)
REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, "refresh_token_expire_days", 7)
MIN_JWT_SECRET_LENGTH = 32


def _load_signing_key() -> str:
    """JWT signing key must be its own secret — never the automation/service secret."""
    key = (settings.jwt_secret or "").strip()
    if len(key) < MIN_JWT_SECRET_LENGTH:
        raise RuntimeError(
            f"JWT_SECRET must be set to a random value of at least {MIN_JWT_SECRET_LENGTH} characters "
            "(e.g. `openssl rand -hex 32`)."
        )
    if settings.automation_shared_secret and hmac.compare_digest(key, settings.automation_shared_secret):
        raise RuntimeError("JWT_SECRET must differ from AUTOMATION_SHARED_SECRET.")
    return key


SECRET_KEY = _load_signing_key()


# ── Password hashing ─────────────────────────────────────────────────────────

_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def _bcrypt_input(password: str) -> bytes:
    # bcrypt only reads the first 72 bytes; pre-hash so long passwords are not truncated.
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def _legacy_hash(password: str) -> str:
    salt = settings.password_hash_salt
    return hmac.new(salt.encode("utf-8"), password.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_password(password: str) -> str:
    """Hash a password with bcrypt (per-hash random salt, adaptive cost)."""
    return bcrypt.hashpw(_bcrypt_input(password), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time verification of bcrypt hashes and legacy HMAC hashes."""
    if not hashed_password:
        return False
    if hashed_password.startswith(_BCRYPT_PREFIXES):
        try:
            return bcrypt.checkpw(_bcrypt_input(plain_password), hashed_password.encode("ascii"))
        except ValueError:
            return False
    return hmac.compare_digest(_legacy_hash(plain_password), hashed_password)


def password_needs_rehash(hashed_password: str) -> bool:
    """True for legacy (pre-bcrypt) hashes that should be upgraded on next login."""
    return not (hashed_password or "").startswith(_BCRYPT_PREFIXES)


# ── JWT creation / decoding ──────────────────────────────────────────────────

def _encode(payload: Dict[str, Any]) -> str:
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode(token: str, expected_type: str) -> Optional[Dict[str, Any]]:
    """Verify signature + expiry and require the expected token ``type``."""
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
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
    payload.update({
        "iat": now,
        "exp": now + (expires_delta_minutes or ACCESS_TOKEN_EXPIRE_MINUTES) * 60,
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
    if await resilient_store.get(f"auth:session_revoked:{payload['sid']}"):
        return True
    revoked_before = await resilient_store.get(f"auth:user_revoked_before:{payload['sub']}")
    if revoked_before and int(payload.get("iat", 0)) <= int(float(revoked_before)):
        return True
    return False


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
    await resilient_store.set(f"auth:refresh_active:{jti}", "1", expire_seconds=lifetime)
    return _encode(payload)


async def revoke_session(sid: str) -> None:
    lifetime = REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await resilient_store.set(f"auth:session_revoked:{sid}", "1", expire_seconds=lifetime)


async def verify_and_rotate_refresh_token(
    old_token: str,
) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict[str, Any]], str]:
    """Refresh Token Rotation (RTR) with replay detection.

    Returns (is_valid, new_access_token, new_refresh_token, user_payload, message).
    """
    payload = decode_refresh_token(old_token)
    if not payload:
        return False, None, None, None, "Invalid or expired refresh token."
    if await _is_revoked(payload):
        return False, None, None, None, "Session has been revoked."

    jti = payload["jti"]
    lifetime = max(1, int(payload["exp"]) - int(time.time()))

    # Replay: a rotated token presented again => kill the whole session family.
    if await resilient_store.get(f"auth:refresh_used:{jti}"):
        await revoke_session(payload["sid"])
        return False, None, None, None, "Security breach: Replayed refresh token detected. Session revoked."

    if not await resilient_store.get(f"auth:refresh_active:{jti}"):
        return False, None, None, None, "Refresh token expired or unrecognized."

    await resilient_store.delete(f"auth:refresh_active:{jti}")
    await resilient_store.set(f"auth:refresh_used:{jti}", "1", expire_seconds=lifetime)

    user_data = {
        "sub": payload["sub"],
        "email": payload.get("email", ""),
        "role": payload.get("role", "agent"),
        "tenant_id": payload.get("tenant_id") or settings.default_tenant_id,
        "sid": payload["sid"],
    }
    new_access_token = create_access_token(user_data)
    new_refresh_token = await create_refresh_token(user_data)
    return True, new_access_token, new_refresh_token, user_data, "Token rotated successfully."


async def revoke_refresh_token(token: str) -> bool:
    """Logout: revoke the session the refresh token belongs to (also kills its access tokens)."""
    payload = decode_refresh_token(token)
    if not payload:
        return False
    await resilient_store.delete(f"auth:refresh_active:{payload['jti']}")
    await revoke_session(payload["sid"])
    return True


async def revoke_all_user_tokens(user_id: str) -> None:
    """Invalidate every token issued to a user so far (e.g. password change, compromise)."""
    lifetime = REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await resilient_store.set(f"auth:user_revoked_before:{user_id}", str(int(time.time())), expire_seconds=lifetime)
