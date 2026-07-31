"""Authentication endpoints."""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.core.security import create_access_token, get_password_hash, verify_password, get_current_user
from app.core.config import settings
from app.db import get_db
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    credits: int
    plan: str
    xp: int
    level: int


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister):
    async with get_db() as db:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            credits=settings.plans["free"]["credits"]
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

        # Generate token
        token = create_access_token({"sub": str(user.id), "email": user.email})

        return TokenResponse(
            access_token=token,
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "credits": user.credits,
                "plan": user.plan,
                "xp": user.xp,
                "level": user.level
            }
        )


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with get_db() as db:
        result = await db.execute(select(User).where(User.email == form_data.username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token({"sub": str(user.id), "email": user.email})

        return TokenResponse(
            access_token=token,
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "credits": user.credits,
                "plan": user.plan,
                "xp": user.xp,
                "level": user.level
            }
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    async with get_db() as db:
        result = await db.execute(select(User).where(User.id == int(current_user["sub"])))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            credits=user.credits,
            plan=user.plan,
            xp=user.xp,
            level=user.level
        )
