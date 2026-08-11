"""Security utilities: Password hashing and JWT token handling."""

import hashlib
import hmac
import time
from typing import Optional, Dict, Any
from app.config import settings

# JWT secret key from environment or default secret
SECRET_KEY = getattr(settings, "jwt_secret", None) or getattr(settings, "automation_shared_secret", "glg-assets-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    """Hash a plain text password using HMAC SHA256 with salt."""
    salt = "glg_assets_salt_2026"
    return hmac.new(salt.encode('utf-8'), password.encode('utf-8'), hashlib.sha256).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return hash_password(plain_password) == hashed_password


def create_access_token(data: Dict[str, Any], expires_delta_minutes: Optional[int] = None) -> str:
    """Create a signed JWT-like access token."""
    try:
        import jwt
        to_encode = data.copy()
        expire = time.time() + ((expires_delta_minutes or ACCESS_TOKEN_EXPIRE_MINUTES) * 60)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except ImportError:
        # Simple signed token fallback if pyjwt is not installed
        import json
        import base64
        payload = data.copy()
        payload["exp"] = int(time.time() + ((expires_delta_minutes or ACCESS_TOKEN_EXPIRE_MINUTES) * 60))
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
        # Fallback decoder
        try:
            import json
            import base64
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
