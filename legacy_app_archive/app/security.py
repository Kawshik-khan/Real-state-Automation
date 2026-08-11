import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any


class AuthorizationError(Exception):
    pass


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant_id: str | None
    roles: frozenset[str]


def _decode_part(value: str) -> dict[str, Any]:
    padding = "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(value + padding))


def decode_jwt(token: str, secret: str) -> Principal:
    """Small HS256 hook; production deployments should use an OIDC/JWKS adapter."""
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthorizationError("Invalid bearer token")
    header, payload, signature = parts
    if _decode_part(header).get("alg") != "HS256":
        raise AuthorizationError("Unsupported token algorithm")
    expected = hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    actual = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
    if not hmac.compare_digest(expected, actual):
        raise AuthorizationError("Invalid bearer token")
    claims = _decode_part(payload)
    subject = claims.get("sub")
    if not subject:
        raise AuthorizationError("Token subject is required")
    roles = claims.get("roles", claims.get("scope", []))
    if isinstance(roles, str):
        roles = roles.split()
    return Principal(str(subject), claims.get("tenant_id"), frozenset(roles))


def require_role(principal: Principal, role: str) -> None:
    if role not in principal.roles and "admin" not in principal.roles:
        raise AuthorizationError(f"Role '{role}' is required")