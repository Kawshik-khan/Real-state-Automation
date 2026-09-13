"""Auth endpoints for login, user verification, and user management."""

from datetime import datetime
from typing import List

from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import get_current_user, require_roles
from app.models.user import LoginRequest, Token, UserCreate, UserInDB, UserResponse, UserRole
from fastapi import APIRouter, Depends, HTTPException, status

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
async def login(req: LoginRequest):
    """Authenticate user with email & password and return JWT access token."""
    email_clean = req.email.strip().lower()
    user_db = USERS_DB.get(email_clean)

    if not user_db or not verify_password(req.password, user_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user_db.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    token_data = {
        "sub": user_db.id,
        "email": user_db.email,
        "role": user_db.role.value,
        "tenant_id": user_db.tenant_id,
    }
    access_token = create_access_token(token_data)

    user_resp = UserResponse(
        id=user_db.id,
        email=user_db.email,
        full_name=user_db.full_name,
        role=user_db.role,
        tenant_id=user_db.tenant_id,
        is_active=user_db.is_active,
        created_at=user_db.created_at,
    )

    return Token(access_token=access_token, token_type="bearer", user=user_resp)


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
