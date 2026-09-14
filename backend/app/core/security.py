"""Security utilities: Password hashing and JWT token handling."""

import hashlib
import hmac
import time
from typing import Any, Dict, Optional, Tuple

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
    """Hash a plain text password using HMAC SHA256 with salt."""
    salt = settings.password_hash_salt
    return hmac.new(salt.encode('utf-8'), password.encode('utf-8'), hashlib.sha256).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return hash_password(plain_password) == hashed_password


def create_access_token(data: Dict[str, Any], expires_delta_minutes: Optional[int] = None) -> str:
    """Create a signed short-lived JWT access token (default 15 minutes)."""
    try:
        import jwt
        to_encode = data.copy()
        expire = time.time() + ((expires_delta_minutes or ACCESS_TOKEN_EXPIRE_MINUTES) * 60)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except ImportError:
        import base64
        import json
        payload = data.copy()
        payload["exp"] = int(time.time() + ((expires_delta_minutes or ACCESS_TOKEN_EXPIRE_MINUTES) * 60))
        payload["type"] = "access"
        encoded_bytes = base64.urlsafe_b64encode(json.dumps(payload).encode())
        sig = hmac.new(SECRET_KEY.encode(), encoded_bytes, hashlib.sha256).hexdigest()
        return f"{encoded_bytes.decode()}.{sig}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify access token."""
    try:
        import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        try:
            import base64
            import json
            parts = token.split(".")
            if len(parts) != 2:
                return None
            payload_b64, sig = parts
            expected_sig = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected_sig):
                return None
            payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
            if payload.get("exp", 0) < time.time():
                return None
            return payload
        except Exception:
            return None


def create_refresh_token(data: Dict[str, Any], expires_delta_days: Optional[int] = None) -> str:
    """Create a cryptographically signed refresh token (7 days) with unique jti identifier."""
    import uuid
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

    # Record in active tokens registry
    _active_refresh_tokens[jti] = {
        "sub": sub,
        "role": role,
        "email": data.get("email", ""),
        "expires_at": expires_at,
    }

    try:
        import jwt
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    except ImportError:
        import base64
        import json
        payload_copy = payload.copy()
        payload_copy["exp"] = int(expires_at)
        encoded_bytes = base64.urlsafe_b64encode(json.dumps(payload_copy).encode())
        sig = hmac.new(SECRET_KEY.encode(), encoded_bytes, hashlib.sha256).hexdigest()
        return f"{encoded_bytes.decode()}.{sig}"


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify refresh token."""
    payload = decode_access_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


def verify_and_rotate_refresh_token(old_token: str) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict[str, Any]], str]:
    """Execute Refresh Token Rotation (RTR).
    
    If the provided token was previously used (replayed), revokes all sessions for that user.
    On success, issues a fresh 15-minute access token and rotated 7-day refresh token.
    Returns (is_valid, new_access_token, new_refresh_token, user_payload, message).
    """
    payload = decode_refresh_token(old_token)
    if not payload:
        return False, None, None, None, "Invalid or expired refresh token."

    jti = payload.get("jti")
    sub = payload.get("sub")

    # 1. Replay attack detection
    if jti in _revoked_refresh_tokens:
        # Revoke all tokens for this user family
        revoke_all_user_tokens(sub)
        return False, None, None, None, "Security breach: Replayed refresh token detected. All sessions revoked."

    # 2. Check active token presence
    if jti not in _active_refresh_tokens:
        return False, None, None, None, "Refresh token expired or unrecognized."

    # 3. Rotate: Revoke the old jti immediately
    _active_refresh_tokens.pop(jti, None)
    _revoked_refresh_tokens.add(jti)

    # 4. Generate new tokens
    user_data = {
        "sub": sub,
        "role": payload.get("role", "agent"),
        "email": payload.get("email", ""),
    }
    new_access_token = create_access_token(user_data)
    new_refresh_token = create_refresh_token(user_data)

    return True, new_access_token, new_refresh_token, user_data, "Token rotated successfully."


def revoke_refresh_token(token: str) -> bool:
    """Revoke a single refresh token."""
    payload = decode_refresh_token(token)
    if payload:
        jti = payload.get("jti")
        if jti:
            _active_refresh_tokens.pop(jti, None)
            _revoked_refresh_tokens.add(jti)
            return True
    return False


def revoke_all_user_tokens(user_id: str) -> int:
    """Revoke all active refresh tokens for a user (e.g. after password change or security breach)."""
    revoked_count = 0
    jtis_to_remove = [
        jti for jti, info in _active_refresh_tokens.items() if info.get("sub") == user_id
    ]
    for jti in jtis_to_remove:
        _active_refresh_tokens.pop(jti, None)
        _revoked_refresh_tokens.add(jti)
        revoked_count += 1
    return revoked_count

