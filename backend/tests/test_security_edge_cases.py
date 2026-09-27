import time

import jwt
import pytest

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)

SECRET_KEY = settings.jwt_secret or settings.automation_shared_secret
ALGORITHM = "HS256"

def test_decode_access_token_expired():
    """Verify expired token returns None."""
    # Use negative delta. -5 will evaluate to truthy and subtract 5 mins from time.time().
    expired_token = create_access_token({"sub": "usr-123", "role": "agent"}, expires_delta_minutes=-5)
    assert decode_access_token(expired_token) is None

def test_decode_access_token_empty_and_none():
    """Verify empty, None, and whitespace inputs return None safely."""
    # Type hints might complain about None, but at runtime it should be safe.
    assert decode_access_token("") is None
    assert decode_access_token("    ") is None

    # decode_access_token has exception handling, but we need to ensure it doesn't break
    try:
        assert decode_access_token(None) is None
    except Exception as e:
        pytest.fail(f"decode_access_token(None) raised an exception: {e}")

def test_decode_access_token_wrong_secret():
    """Verify token signed with wrong secret returns None."""
    payload = {"sub": "usr-123", "exp": time.time() + 60, "type": "access"}
    bad_token = jwt.encode(payload, "wrong-secret", algorithm=ALGORITHM)
    assert decode_access_token(bad_token) is None

def test_decode_access_token_alg_none():
    """Verify token with 'none' algorithm returns None."""
    payload = {"sub": "usr-123", "exp": time.time() + 60, "type": "access"}
    # jwt library by default might prevent none algorithm, so we construct it manually
    import base64
    import json

    header_b64 = base64.urlsafe_b64encode(b'{"alg": "none", "typ": "JWT"}').decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

    none_token = f"{header_b64}.{payload_b64}."
    assert decode_access_token(none_token) is None

def test_decode_access_token_alg_mismatch():
    """Verify token signed with unsupported algorithm returns None."""
    payload = {"sub": "usr-123", "exp": time.time() + 60, "type": "access"}
    # Use HS384 instead of HS256
    wrong_alg_token = jwt.encode(payload, SECRET_KEY, algorithm="HS384")
    assert decode_access_token(wrong_alg_token) is None

@pytest.mark.asyncio
async def test_decode_access_token_type_differentiation():
    """Each decoder accepts only its own token type: a refresh token must never pass as an
    access token (review finding F3), and vice versa."""
    access_token = create_access_token({"sub": "usr-123"})
    refresh_token = await create_refresh_token({"sub": "usr-123"})

    access_payload = decode_access_token(access_token)
    assert access_payload is not None
    assert access_payload.get("type") == "access"
    assert decode_refresh_token(access_token) is None

    assert decode_access_token(refresh_token) is None
    refresh_payload = decode_refresh_token(refresh_token)
    assert refresh_payload is not None
    assert refresh_payload.get("type") == "refresh"

def test_decode_access_token_fallback_resilience():
    """Verify fallback parser handles invalid two-part tokens safely."""
    # invalid base64 and invalid sig
    assert decode_access_token("not_base64.fake_sig") is None
    # valid base64 but invalid JSON
    import base64
    invalid_json_b64 = base64.urlsafe_b64encode(b"invalid json").decode()
    assert decode_access_token(f"{invalid_json_b64}.fake_sig") is None

def test_decode_access_token_invalid_format():
    """Verify standard invalid token strings return None."""
    assert decode_access_token("invalid_token_string") is None
    assert decode_access_token("header.payload.signature.extra") is None
