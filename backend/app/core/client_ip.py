"""Trustworthy client IP resolution.

``X-Forwarded-For`` is client-controlled: only the entries appended by *our own* proxies
can be trusted. Resolution order:

1. ``CLIENT_IP_HEADER`` (e.g. ``CF-Connecting-IP``) — a header the edge proxy *overwrites*,
   so clients cannot forge it. Only set this if the proxy really does overwrite it.
2. ``TRUSTED_PROXY_HOPS=N`` — the N-th ``X-Forwarded-For`` entry from the right (the address
   the outermost trusted proxy saw).
3. Otherwise the socket peer address.

Behind a proxy with neither configured, every request appears to come from the proxy and
IP-based limits apply to all users together. Verify with GET /api/v1/auth/client-ip-diagnostics.
"""

import ipaddress

from fastapi import Request

from app.config import settings


def _valid_ip(value: str) -> str | None:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def get_client_ip(request: Request) -> str:
    peer = request.client.host if request.client and request.client.host else "unknown"

    header_name = (getattr(settings, "client_ip_header", None) or "").strip()
    if header_name:
        resolved = _valid_ip(request.headers.get(header_name, ""))
        if resolved:
            return resolved

    hops = max(0, int(getattr(settings, "trusted_proxy_hops", 0) or 0))
    if hops == 0:
        return peer

    forwarded = request.headers.get("x-forwarded-for", "")
    chain = [part.strip() for part in forwarded.split(",") if part.strip()]
    if len(chain) < hops:
        return peer
    return _valid_ip(chain[-hops]) or peer
