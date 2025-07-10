"""
Authentication endpoints for AIRIES AI Backend
Handles user registration, login, token refresh, and password reset
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from ....core.database import get_db
from ....core.security import (
    create_access_token, create_refresh_token, verify_token,
    verify_password, get_password_hash, SecurityException
)
from ....schemas.user import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    PasswordReset, PasswordResetConfirm, RefreshTokenRequest
)
from ....services.user_service import UserService
from ....services.email_service import EmailService

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user account
    """
    user_service = UserService(db)
    
    # Check if user already exists
    existing_user = await user_service.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    user = await user_service.create_user(user_data)
    
    # Send verification email
    email_service = EmailService()
    await email_service.send_verification_email(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    User login with email and password
    """
    user_service = UserService(db)
    
    # Get user by email
    user = await user_service.get_by_email(user_credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is locked
    if user.is_account_locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to failed login attempts"
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user.hashed_password):
        # Increment failed attempts
        await user_service.increment_failed_attempts(user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Reset failed attempts and update last login
    await user_service.reset_failed_attempts(user.id)
    await user_service.update_last_login(user.id)
    
    # Create tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,  # 30 minutes
        user=user
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    user_id = verify_token(token_data.refresh_token, token_type="refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=1800,  # 30 minutes
        user=user
    )


@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Request password reset email
    """
    user_service = UserService(db)
    user = await user_service.get_by_email(reset_data.email)
    
    if user:
        # Generate reset token and send email
        await user_service.generate_password_reset_token(user.id)
        
        email_service = EmailService()
        await email_service.send_password_reset_email(user)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Confirm password reset with token
    """
    user_service = UserService(db)
    
    # Verify reset token
    user = await user_service.verify_password_reset_token(reset_data.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    hashed_password = get_password_hash(reset_data.new_password)
    await user_service.update_password(user.id, hashed_password)
    
    # Clear reset token
    await user_service.clear_password_reset_token(user.id)
    
    return {"message": "Password has been reset successfully"}


@router.post("/verify-email/{token}")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify user email with verification token
    """
    user_service = UserService(db)
    
    # Verify email token
    user = await user_service.verify_email_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Mark email as verified
    await user_service.mark_email_verified(user.id)
    
    return {"message": "Email has been verified successfully"}


@router.post("/resend-verification")
async def resend_verification_email(
    email_data: PasswordReset,  # Reuse schema for email
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Resend email verification
    """
    user_service = UserService(db)
    user = await user_service.get_by_email(email_data.email)
    
    if user and not user.is_verified:
        # Generate new verification token
        await user_service.generate_verification_token(user.id)
        
        # Send verification email
        email_service = EmailService()
        await email_service.send_verification_email(user)
    
    return {"message": "If the email exists and is unverified, a verification link has been sent"}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current authenticated user from JWT token
    """
    # Verify access token
    user_id = verify_token(credentials.credentials, token_type="access")
    if not user_id:
        raise SecurityException("Invalid or expired token")
    
    # Get user from database
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    if not user:
        raise SecurityException("User not found")
    
    if not user.is_active:
        raise SecurityException("User account is inactive")
    
    return user


# Dependency for getting current active user
def get_current_active_user(current_user: Any = Depends(get_current_user)) -> Any:
    """
    Dependency to get current active user
    """
    return current_user