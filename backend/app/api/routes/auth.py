"""Authentication endpoints: login, register, user management"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db import get_db
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# --- Schemas ---

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str | None = None
    last_name: str | None = None
    role: str = "trainee"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Endpoints ---

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check for existing username or email
    result = await db.execute(
        select(User).where((User.username == request.username) | (User.email == request.email))
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already registered")

    try:
        role = UserRole(request.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {request.role}")

    user = User(
        username=request.username,
        email=request.email,
        password_hash=get_password_hash(request.password),
        role=role,
        first_name=request.first_name,
        last_name=request.last_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"User registered: {user.username} ({user.role.value})")

    return UserResponse(
        id=str(user.id), username=user.username, email=user.email,
        role=user.role.value, first_name=user.first_name, last_name=user.last_name,
        is_active=user.is_active, created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = create_access_token(user.id, user.role.value)
    logger.info(f"User logged in: {user.username}")
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserResponse(
        id=str(user.id), username=user.username, email=user.email,
        role=user.role.value, first_name=user.first_name, last_name=user.last_name,
        is_active=user.is_active, created_at=user.created_at,
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPERVISOR)),
):
    """List all users (supervisor/admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        UserResponse(
            id=str(u.id), username=u.username, email=u.email,
            role=u.role.value, first_name=u.first_name, last_name=u.last_name,
            is_active=u.is_active, created_at=u.created_at,
        )
        for u in users
    ]
