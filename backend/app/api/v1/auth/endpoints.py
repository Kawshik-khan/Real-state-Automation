"""Auth endpoints for login, user verification, and user management."""

from datetime import datetime
from typing import List, Optional

from app.core.rate_limiter import AUTH_LOGIN_LIMIT, limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
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
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

router = APIRouter(prefix="/auth", tags=["Auth"])

# In-memory demo user database seeded with Admin, Manager, Agent, Viewer
USERS_DB: dict[str, UserInDB] = {
    "admin@glgassets.com": UserInDB(
        id="usr-admin-001",
        email="admin@glgassets.com",
        full_name="Alex Mercer (Admin)",
        role=UserRole.ADMIN,
        tenant_id="glg-default",
        is_active=True,
        hashed_password=hash_password("admin123"),
        created_at=datetime.utcnow().isoformat(),
    ),
    "manager@glgassets.com": UserInDB(
        id="usr-manager-002",
        email="manager@glgassets.com",
        full_name="Sarah Connor (Manager)",
        role=UserRole.MANAGER,
        tenant_id="glg-default",
        is_active=True,
        hashed_password=hash_password("manager123"),
        created_at=datetime.utcnow().isoformat(),
    ),
    "agent@glgassets.com": UserInDB(
        id="usr-agent-003",
        email="agent@glgassets.com",
        full_name="Rahul Sharma (Agent)",
        role=UserRole.AGENT,
        tenant_id="glg-default",
        is_active=True,
        hashed_password=hash_password("agent123"),
        created_at=datetime.utcnow().isoformat(),
    ),
    "developer@glgassets.com": UserInDB(
        id="usr-dev-005",
        email="developer@glgassets.com",
        full_name="Alex Chen (Dev Lead)",
        role=UserRole.DEVELOPER,
        tenant_id="glg-default",
        is_active=True,
        hashed_password=hash_password("dev123"),
        created_at=datetime.utcnow().isoformat(),
    ),
    "viewer@glgassets.com": UserInDB(
        id="usr-viewer-004",
        email="viewer@glgassets.com",
        full_name="Guest Stakeholder (Viewer)",
        role=UserRole.VIEWER,
        tenant_id="glg-default",
        is_active=True,
        hashed_password=hash_password("viewer123"),
        created_at=datetime.utcnow().isoformat(),
    ),
}


@router.post("/login", response_model=Token)
@limiter.limit(AUTH_LOGIN_LIMIT)
async def login(request: Request, response: Response, req: LoginRequest):
    """Authenticate user with email & password and return access token + refresh token."""
    email_clean = req.email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    if request.headers.get("x-forwarded-for"):
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

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

    user_db = USERS_DB.get(email_clean)

    if not user_db or not verify_password(req.password, user_db.hashed_password):
        attempts, delay, newly_locked = await account_lockout.record_failure(email_clean, client_ip)
        if newly_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked due to multiple failed login attempts. Please try again in 15 minutes.",
                headers={"Retry-After": "900"},
            )
        if delay > 0:
            import asyncio
            await asyncio.sleep(delay)

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
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Set secure HttpOnly cookie for refresh token
    is_secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.set_cookie(
        key="glg_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=7 * 86400,
        path="/",
    )

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
    raw_token = None
    if body and body.refresh_token:
        raw_token = body.refresh_token.strip()
    if not raw_token:
        raw_token = request.cookies.get("glg_refresh_token")

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required in cookie or body.",
        )

    is_valid, new_access, new_refresh, user_payload, msg = verify_and_rotate_refresh_token(raw_token)
    if not is_valid or not new_access:
        response.delete_cookie(key="glg_refresh_token", path="/")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
        )

    # Set rotated HttpOnly cookie
    is_secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.set_cookie(
        key="glg_refresh_token",
        value=new_refresh,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=7 * 86400,
        path="/",
    )

    user_email = user_payload.get("email") if user_payload else None
    user_db = USERS_DB.get(user_email) if user_email else None
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
    raw_token = None
    if body and body.refresh_token:
        raw_token = body.refresh_token.strip()
    if not raw_token:
        raw_token = request.cookies.get("glg_refresh_token")

    if raw_token:
        revoke_refresh_token(raw_token)

    response.delete_cookie(key="glg_refresh_token", path="/")
    return {"success": True, "message": "Successfully logged out and session revoked."}



@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return currently authenticated user profile."""
    email = current_user.get("email")
    user_db = USERS_DB.get(email) if email else None
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
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            tenant_id=u.tenant_id,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in USERS_DB.values()
    ]


@router.post("/register", response_model=UserResponse)
async def register_user(
    new_user: UserCreate,
    current_user: dict = Depends(require_roles([UserRole.ADMIN])),
):
    """Create a new system user (Admin only)."""
    email_clean = new_user.email.strip().lower()
    if email_clean in USERS_DB:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    usr_id = f"usr-{len(USERS_DB) + 1:03d}"
    user_db = UserInDB(
        id=usr_id,
        email=email_clean,
        full_name=new_user.full_name,
        role=new_user.role,
        tenant_id=new_user.tenant_id,
        is_active=new_user.is_active,
        hashed_password=hash_password(new_user.password),
        created_at=datetime.utcnow().isoformat(),
    )
    USERS_DB[email_clean] = user_db

    return UserResponse(
        id=user_db.id,
        email=user_db.email,
        full_name=user_db.full_name,
        role=user_db.role,
        tenant_id=user_db.tenant_id,
        is_active=user_db.is_active,
        created_at=user_db.created_at,
    )


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

