"""Security utilities: Password hashing and JWT token handling."""

import hashlib
import hmac
import time
from typing import Any, Dict, Optional, Tuple

import jwt

from app.config import settings

# JWT settings
SECRET_KEY = settings.jwt_secret or settings.automation_shared_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "access_token_expire_minutes", 15)  # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, "refresh_token_expire_days", 7)       # 7 days

# In-memory registry for active & revoked refresh tokens (backed by resilient store)
_active_refresh_tokens: Dict[str, Dict[str, Any]] = {}  # jti -> {sub, role, created_at, expires_at}
_revoked_refresh_tokens: set = set()                     # set of revoked jti strings


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt with per-hash unique salt.

    bcrypt automatically generates a unique salt per hash and applies
    a configurable work factor (default 12 rounds ≈ ~250ms per hash),
    making brute-force and rainbow table attacks computationally infeasible.
    """
    from passlib.hash import bcrypt
    return bcrypt.using(rounds=12).hash(password)


def _hash_password_legacy(password: str) -> str:
    """Legacy HMAC-SHA256 hasher — used ONLY for verifying old hashes during migration."""
    salt = settings.password_hash_salt
    return hmac.new(salt.encode('utf-8'), password.encode('utf-8'), hashlib.sha256).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password.

    Transparently supports both:
    - New bcrypt hashes (prefix: $2b$ or $2a$)
    - Legacy HMAC-SHA256 hex hashes (64-char hex strings) for migration compatibility
    """
    if hashed_password.startswith(("$2b$", "$2a$", "$2y$")):
        from passlib.hash import bcrypt
        return bcrypt.verify(plain_password, hashed_password)
    # Legacy fallback: HMAC-SHA256 hash (will be phased out after full migration)
    return hmac.compare_digest(_hash_password_legacy(plain_password), hashed_password)



def create_access_token(data: Dict[str, Any], expires_delta_minutes: Optional[int] = None) -> str:
    """Create a signed short-lived JWT access token (default 15 minutes)."""
    to_encode = data.copy()
    expire = time.time() + ((expires_delta_minutes or ACCESS_TOKEN_EXPIRE_MINUTES) * 60)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify access token using PyJWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


async def create_refresh_token(data: Dict[str, Any], expires_delta_days: Optional[int] = None) -> str:
    """Create a cryptographically signed refresh token (7 days) with unique jti identifier."""
    import uuid

    from app.core.token_store import token_store

    jti = str(uuid.uuid4())
    sub = data.get("sub", "unknown")
    role = data.get("role", "agent")
    expires_at = time.time() + ((expires_delta_days or REFRESH_TOKEN_EXPIRE_DAYS) * 86400)

    payload = {
        "sub": sub,
        "role": role,
        "email": data.get("email", ""),
        "type": "refresh",
        "jti": jti,
        "exp": expires_at,
    }

    # Record in active tokens registry (in-memory + distributed token store)
    _active_refresh_tokens[jti] = {
        "sub": sub,
        "role": role,
        "email": data.get("email", ""),
        "expires_at": expires_at,
    }
    await token_store.record_active_token(
        jti=jti,
        user_id=sub,
        role=role,
        email=data.get("email", ""),
        expires_at=expires_at,
    )

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify refresh token."""
    payload = decode_access_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


async def verify_and_rotate_refresh_token(
    old_token: str,
) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict[str, Any]], str]:
    """Execute Refresh Token Rotation (RTR) backed by distributed token store.
    
    If the provided token was previously used (replayed), revokes all sessions for that user.
    On success, issues a fresh 15-minute access token and rotated 7-day refresh token.
    Returns (is_valid, new_access_token, new_refresh_token, user_payload, message).
    """
    from app.core.token_store import token_store

    payload = decode_refresh_token(old_token)
    if not payload:
        return False, None, None, None, "Invalid or expired refresh token."

    jti = payload.get("jti")
    sub = payload.get("sub")
    exp = payload.get("exp", time.time() + 86400)

    if not jti or not sub:
        return False, None, None, None, "Malformed refresh token claims."

    # 1. Replay attack detection: Check distributed blacklist (Memory -> Redis -> PostgreSQL)
    is_revoked = (jti in _revoked_refresh_tokens) or (await token_store.is_token_revoked(jti, user_id=sub))
    if is_revoked:
        # Revoke all tokens for this user family across all workers
        await revoke_all_user_tokens(sub)
        return False, None, None, None, "Security breach: Replayed refresh token detected. All sessions revoked."

    # 2. Check active token presence in distributed store
    active_token = (jti in _active_refresh_tokens) or (await token_store.get_active_token(jti) is not None)
    if not active_token:
        return False, None, None, None, "Refresh token expired or unrecognized."

    # 3. Rotate: Revoke the old jti immediately
    _active_refresh_tokens.pop(jti, None)
    _revoked_refresh_tokens.add(jti)
    await token_store.revoke_token(jti, sub, exp, reason="rotation")

    # 4. Generate new tokens
    user_data = {
        "sub": sub,
        "role": payload.get("role", "agent"),
        "email": payload.get("email", ""),
    }
    new_access_token = create_access_token(user_data)
    new_refresh_token = await create_refresh_token(user_data)

    return True, new_access_token, new_refresh_token, user_data, "Token rotated successfully."


async def revoke_refresh_token(token: str) -> bool:
    """Revoke a single refresh token."""
    from app.core.token_store import token_store

    payload = decode_refresh_token(token)
    if payload:
        jti = payload.get("jti")
        sub = payload.get("sub", "unknown")
        exp = payload.get("exp", time.time() + 86400)
        if jti:
            _active_refresh_tokens.pop(jti, None)
            _revoked_refresh_tokens.add(jti)
            await token_store.revoke_token(jti, sub, exp, reason="logout")
            return True
    return False


async def revoke_all_user_tokens(user_id: str) -> int:
    """Revoke all active refresh tokens for a user across all worker instances."""
    from app.core.token_store import token_store

    revoked_count = 0
    jtis_to_remove = [
        jti for jti, info in _active_refresh_tokens.items() if info.get("sub") == user_id
    ]
    for jti in jtis_to_remove:
        _active_refresh_tokens.pop(jti, None)
        _revoked_refresh_tokens.add(jti)
        revoked_count += 1

    distributed_count = await token_store.revoke_all_user_tokens(user_id, reason="admin_or_security")
    return max(revoked_count, distributed_count)

