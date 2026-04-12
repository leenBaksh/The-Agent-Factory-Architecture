"""
Authentication API router.
Handles login, registration, token refresh, and 2FA.
"""

import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel, EmailStr, Field

from app.config import get_settings
from app.utils.password import PasswordValidator, hash_password, verify_password
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    TokenResponse,
    get_expires_in_seconds
)
from app.utils.rate_limiter import (
    login_rate_limiter,
    verify_2fa_rate_limiter,
    check_rate_limit
)
from app.utils.two_factor import two_factor_auth, TwoFactorAuth

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── In-memory user store (replace with database in production) ─────────────────

# Pre-populated with default admin user
_users_db = {
    "admin@agentfactory.com": {
        "id": "1",
        "email": "admin@agentfactory.com",
        "name": "Admin User",
        "role": "Administrator",
        # Password: Admin@123 (hashed with bcrypt)
        "password_hash": hash_password("Admin@123"),
        "two_factor_enabled": False,
    }
}


# ── Request/Response Models ────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    success: bool
    message: str
    requires_2fa: bool = False
    temp_token: Optional[str] = None
    tokens: Optional[TokenResponse] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class Verify2FARequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    temp_token: str


class Setup2FAResponse(BaseModel):
    success: bool
    secret: str
    otpauth_uri: str
    message: str


class Verify2FASetupRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class Disable2FARequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    email: EmailStr
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── Utility Functions ──────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user from database by email."""
    return _users_db.get(email)


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate user with email and password."""
    user = get_user_by_email(email)
    if not user:
        return None
    
    if not verify_password(password, user["password_hash"]):
        return None
    
    return user


# ── Login Endpoint ─────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request):
    """
    Authenticate user and return JWT tokens.
    Rate limited to prevent brute force attacks.
    """
    # Check rate limit
    client_ip = http_request.client.host
    check_rate_limit(login_rate_limiter, f"login:{client_ip}")

    # Authenticate user
    user = authenticate_user(request.email, request.password)
    
    if not user:
        # Don't reveal if email exists or not
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if 2FA is enabled
    if two_factor_auth.is_enabled(request.email):
        # Return temporary token for 2FA verification
        from app.utils.jwt import create_refresh_token as create_temp_token
        temp_token = create_temp_token(
            user_id=user["id"],
            email=user["email"],
            expires_delta=timedelta(minutes=5)
        )
        
        return LoginResponse(
            success=True,
            message="2FA verification required",
            requires_2fa=True,
            temp_token=temp_token
        )

    # Generate tokens
    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        expires_delta=timedelta(minutes=settings.jwt_access_token_minutes)
    )
    
    refresh_token = create_refresh_token(
        user_id=user["id"],
        email=user["email"],
        expires_delta=timedelta(days=settings.jwt_refresh_token_days)
    )

    logger.info(f"User logged in: {user['email']}")

    return LoginResponse(
        success=True,
        message="Login successful",
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=get_expires_in_seconds(timedelta(minutes=settings.jwt_access_token_minutes))
        )
    )


# ── Token Refresh Endpoint ─────────────────────────────────────────────────────

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    # Decode and validate refresh token
    token_data = decode_token(request.refresh_token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Get user
    user = get_user_by_email(token_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Generate new access token
    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        expires_delta=timedelta(minutes=settings.jwt_access_token_minutes)
    )

    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": get_expires_in_seconds(timedelta(minutes=settings.jwt_access_token_minutes))
    }


# ── Verify 2FA Endpoint ────────────────────────────────────────────────────────

@router.post("/verify-2fa", response_model=LoginResponse)
async def verify_2fa(request: Verify2FARequest, http_request: Request):
    """
    Verify 2FA code and return JWT tokens.
    Rate limited to prevent brute force attacks.
    """
    # Check rate limit
    client_ip = http_request.client.host
    check_rate_limit(verify_2fa_rate_limiter, f"verify2fa:{client_ip}")

    # Decode temp token
    temp_data = decode_token(request.temp_token)
    if not temp_data or temp_data.email != request.email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired temporary token"
        )

    # Verify 2FA code
    if not two_factor_auth.verify_code(request.email, request.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA code"
        )

    # Get user
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Generate tokens
    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        expires_delta=timedelta(minutes=settings.jwt_access_token_minutes)
    )
    
    refresh_token = create_refresh_token(
        user_id=user["id"],
        email=user["email"],
        expires_delta=timedelta(days=settings.jwt_refresh_token_days)
    )

    logger.info(f"User 2FA verified and logged in: {user['email']}")

    return LoginResponse(
        success=True,
        message="Login successful",
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=get_expires_in_seconds(timedelta(minutes=settings.jwt_access_token_minutes))
        )
    )


# ── 2FA Setup Endpoints ────────────────────────────────────────────────────────

@router.post("/2fa/setup", response_model=Setup2FAResponse)
async def setup_2fa(email: EmailStr):
    """Setup 2FA for a user."""
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    secret, otpauth_uri = two_factor_auth.setup_2fa(email)

    return Setup2FAResponse(
        success=True,
        secret=secret,
        otpauth_uri=otpauth_uri,
        message="Scan the QR code with your authenticator app"
    )


@router.post("/2fa/verify-setup")
async def verify_2fa_setup(request: Verify2FASetupRequest):
    """Verify 2FA setup completion."""
    if not two_factor_auth.verify_setup(request.email, request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA code. Please try again."
        )

    return {
        "success": True,
        "message": "2FA setup completed successfully"
    }


@router.post("/2fa/disable")
async def disable_2fa(request: Disable2FARequest):
    """Disable 2FA for a user (requires password verification)."""
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    two_factor_auth.disable_2fa(request.email)

    return {
        "success": True,
        "message": "2FA disabled successfully"
    }


# ── Change Password Endpoint ───────────────────────────────────────────────────

@router.post("/change-password")
async def change_password(request: ChangePasswordRequest):
    """Change user password."""
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not verify_password(request.current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Validate new password
    validation_error = PasswordValidator.validate(request.new_password)
    if validation_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error
        )

    # Update password
    user["password_hash"] = hash_password(request.new_password)

    return {
        "success": True,
        "message": "Password changed successfully"
    }
