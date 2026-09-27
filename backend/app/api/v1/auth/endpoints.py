"""Auth endpoints for login, user verification, and user management."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool

from app.config import settings
from app.core.client_ip import get_client_ip
from app.core.rate_limiter import AUTH_LOGIN_LIMIT, limiter
from app.core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    STREAM_TICKET_TTL_SECONDS,
    create_access_token,
    create_refresh_token,
    create_stream_ticket,
    hash_password,
    revoke_refresh_token,
    verify_and_rotate_refresh_token,
    verify_password,
)
from app.dependencies import get_current_user, require_roles
from app.models.user import (
    LoginRequest,
    RefreshTokenRequest,
    Token,
    UnlockAccountRequest,
    UserCreate,
    UserInDB,
    UserResponse,
    UserRole,
)
from app.services.user_service import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])

# S-03: Resilient in-memory users cache backed by PostgreSQL `auth_users` table
USERS_DB: dict[str, UserInDB] = user_service.in_memory_users

_DUMMY_HASH = hash_password("timing-equalisation-dummy-password")

REFRESH_COOKIE = "glg_refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"  # only sent to auth endpoints, never to the rest of the API
CSRF_HEADER = "X-GLG-Client"


def _set_refresh_cookie(request: Request, response: Response, token: str) -> None:
    secure = settings.refresh_cookie_secure
    if secure is None:
        secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    samesite = (settings.refresh_cookie_samesite or "lax").lower()
    if samesite == "none":
        secure = True  # browsers reject SameSite=None without Secure
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
    response.delete_cookie(key=REFRESH_COOKIE, path="/")  # cookie set by older releases


def _refresh_token_from(request: Request, body: Optional[RefreshTokenRequest]) -> Optional[str]:
    """Body token (API clients) or cookie (browsers). Cookie-authenticated calls must carry a
    custom header: cross-site pages cannot add one without a CORS preflight, which blocks CSRF."""
    if body and body.refresh_token and body.refresh_token.strip():
        return body.refresh_token.strip()
    cookie_token = request.cookies.get(REFRESH_COOKIE)
    if cookie_token and not request.headers.get(CSRF_HEADER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{CSRF_HEADER} header required")
    return cookie_token


@router.post("/login", response_model=Token)
@limiter.limit(AUTH_LOGIN_LIMIT)
async def login(request: Request, response: Response, req: LoginRequest):
    """Authenticate user with email & password and return access token + refresh token."""
    email_clean = req.email.strip().lower()
    client_ip = get_client_ip(request)

    from app.core.account_lockout import account_lockout

    # Check if account or IP is currently locked out
    is_locked, remaining_secs = await account_lockout.check_lockout(email_clean, client_ip)
    if is_locked:
        remaining_mins = max(1, (remaining_secs + 59) // 60)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account temporarily locked due to multiple failed login attempts. Please try again in {remaining_mins} minute(s).",
            headers={"Retry-After": str(remaining_secs)},
        )

    user_db = await user_service.get_user_by_email(email_clean)
    # Always run one bcrypt check (dummy hash for unknown users) so response timing does not
    # reveal which emails exist; bcrypt is CPU-bound, so keep it off the event loop.
    password_ok = await run_in_threadpool(
        verify_password, req.password, user_db.hashed_password if user_db else _DUMMY_HASH
    )

    if not user_db or not password_ok:
        attempts, newly_locked = await account_lockout.record_failure(email_clean, client_ip)
        if newly_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Too many failed login attempts from this network. Please try again in 15 minutes.",
                headers={"Retry-After": "900"},
            )

        remaining_attempts = max(0, 5 - attempts)
        warn_msg = f" ({remaining_attempts} attempts remaining before temporary lockout.)" if attempts >= 3 else ""
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid email or password{warn_msg}",
        )

    if not user_db.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Clear failed attempt counter on success
    await account_lockout.record_success(email_clean, client_ip)

    token_data = {
        "sub": user_db.id,
        "email": user_db.email,
        "role": user_db.role.value,
        "tenant_id": user_db.tenant_id,
        "sid": str(uuid.uuid4()),
    }
    access_token = create_access_token(token_data)
    refresh_token = await create_refresh_token(token_data)

    _set_refresh_cookie(request, response, refresh_token)

    user_resp = UserResponse(
        id=user_db.id,
        email=user_db.email,
        full_name=user_db.full_name,
        role=user_db.role,
        tenant_id=user_db.tenant_id,
        is_active=user_db.is_active,
        created_at=user_db.created_at,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        expires_in=900,
        user=user_resp,
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_access_token(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = None,
):
    """Rotate refresh token and issue fresh 15-minute access token (RTR).
    
    Accepts refresh token via HttpOnly cookie or request body JSON.
    Detects replay attacks and revokes compromised sessions automatically.
    """
    raw_token = _refresh_token_from(request, body)

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required in cookie or body.",
        )

    is_valid, new_access, new_refresh, user_payload, msg = await verify_and_rotate_refresh_token(raw_token)
    if not is_valid or not new_access:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
        )

    _set_refresh_cookie(request, response, new_refresh)

    user_email = user_payload.get("email") if user_payload else None
    user_db = await user_service.get_user_by_email(user_email) if user_email else None
    user_resp = None
    if user_db:
        user_resp = UserResponse(
            id=user_db.id,
            email=user_db.email,
            full_name=user_db.full_name,
            role=user_db.role,
            tenant_id=user_db.tenant_id,
            is_active=user_db.is_active,
            created_at=user_db.created_at,
        )

    return Token(
        access_token=new_access,
        token_type="bearer",
        refresh_token=new_refresh,
        expires_in=900,
        user=user_resp,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = None,
):
    """Revoke active refresh token and clear authentication cookies."""
    raw_token = _refresh_token_from(request, body)

    if raw_token:
        await revoke_refresh_token(raw_token)

    _clear_refresh_cookie(response)
    return {"success": True, "message": "Successfully logged out and session revoked."}



@router.get("/client-ip-diagnostics", summary="Show how the server resolves your client IP (admin)")
async def client_ip_diagnostics(
    request: Request,
    current_user: dict = Depends(require_roles([UserRole.ADMIN, UserRole.DEVELOPER])),
):
    """Deployment check for TRUSTED_PROXY_HOPS / CLIENT_IP_HEADER: the resolved IP should be
    your real public IP. If it is a proxy/internal address, login rate limits and lockouts
    are being shared by all users."""
    return {
        "resolved_client_ip": get_client_ip(request),
        "socket_peer": request.client.host if request.client else None,
        "x_forwarded_for": request.headers.get("x-forwarded-for"),
        "configured_client_ip_header": settings.client_ip_header,
        "configured_header_value": request.headers.get(settings.client_ip_header) if settings.client_ip_header else None,
        "trusted_proxy_hops": settings.trusted_proxy_hops,
    }


@router.post("/stream-ticket", summary="Issue a 60-second ticket for EventSource/WebSocket URLs")
@limiter.limit("60/minute")
async def issue_stream_ticket(request: Request, current_user: dict = Depends(get_current_user)):
    """Browsers cannot attach an Authorization header to EventSource/WebSocket, so they
    exchange their access token for a short-lived, stream-only ticket passed as ``?ticket=``."""
    if current_user.get("is_service"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Stream tickets are for user sessions")
    return {"ticket": create_stream_ticket(current_user), "expires_in": STREAM_TICKET_TTL_SECONDS}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return currently authenticated user profile."""
    email = current_user.get("email")
    user_db = await user_service.get_user_by_email(email) if email else None
    if not user_db:
        raise HTTPException(status_code=404, detail="User profile not found")

    return UserResponse(
        id=user_db.id,
        email=user_db.email,
        full_name=user_db.full_name,
        role=user_db.role,
        tenant_id=user_db.tenant_id,
        is_active=user_db.is_active,
        created_at=user_db.created_at,
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: dict = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.DEVELOPER]))):
    """List all registered platform users (Admin, Manager & Developer)."""
    return await user_service.list_all_users()


@router.post("/register", response_model=UserResponse)
async def register_user(
    new_user: UserCreate,
    current_user: dict = Depends(require_roles([UserRole.ADMIN])),
):
    """Create a new system user (Admin only)."""
    return await user_service.create_user(new_user)


@router.post("/unlock", summary="Unlock account locked by brute force defense")
async def unlock_user_account(
    req: UnlockAccountRequest,
    current_user: dict = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER])),
):
    """Manually unlock an account locked by brute force defenses (Admin/Manager only)."""
    from app.core.account_lockout import account_lockout
    cleared = await account_lockout.unlock_account(req.email)
    return {
        "success": True,
        "message": f"Account '{req.email}' unlocked successfully.",
        "records_cleared": cleared,
    }


@router.get("/locked-accounts", summary="List accounts locked by brute force protection")
async def list_locked_accounts(
    current_user: dict = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.DEVELOPER])),
):
    """List active temporarily locked accounts."""
    from app.core.account_lockout import account_lockout
    return {
        "success": True,
        "locked_accounts": account_lockout.get_locked_accounts(),
    }

