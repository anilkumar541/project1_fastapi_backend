from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import send_password_reset_email
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_password_reset_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.password_reset import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.token import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(token=refresh_token, user_id=user.id, expires_at=expires_at))
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == payload.refresh_token,
            RefreshToken.revoked.is_(False),
        )
    )
    token_row = result.scalar_one_or_none()
    if token_row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or already revoked token",
        )
    token_row.revoked = True
    await db.commit()
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is not None:
        token = generate_password_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )
        db.add(PasswordResetToken(token=token, user_id=user.id, expires_at=expires_at))
        await db.commit()

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        await send_password_reset_email(user.email, reset_url)

    # Always return generic message to prevent user enumeration
    return {"message": "If that email exists, a reset link has been sent"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == payload.token,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > now,
        )
    )
    token_row = result.scalar_one_or_none()
    if token_row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already used reset token",
        )

    user_result = await db.execute(select(User).where(User.id == token_row.user_id))
    user = user_result.scalar_one()
    user.hashed_password = hash_password(payload.new_password)
    token_row.used = True
    await db.commit()

    return {"message": "Password reset successfully"}
