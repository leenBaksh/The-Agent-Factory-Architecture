"""
JWT token generation and validation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


class TokenData(BaseModel):
    """Data contained in JWT token."""
    user_id: str
    email: str
    name: str
    role: str
    exp: datetime


class TokenResponse(BaseModel):
    """Response structure for token generation."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(
    user_id: str,
    email: str,
    name: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_minutes)

    payload = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "role": role,
        "exp": expire,
        "type": "access"
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def create_refresh_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_days)

    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expire,
        "type": "refresh"
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        user_id = payload.get("user_id")
        email = payload.get("email")
        name = payload.get("name")
        role = payload.get("role")
        exp = payload.get("exp")

        if user_id is None or email is None:
            return None

        return TokenData(
            user_id=user_id,
            email=email,
            name=name or "",
            role=role or "user",
            exp=datetime.fromtimestamp(exp, tz=timezone.utc)
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_expires_in_seconds(expires_delta: timedelta) -> int:
    """Get expiration time in seconds."""
    return int(expires_delta.total_seconds())
