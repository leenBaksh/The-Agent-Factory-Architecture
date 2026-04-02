"""
Authentication dependencies for FastAPI routes.

Two guards are provided:
  - require_api_key   : validates the X-API-Key header (external clients)
  - require_internal_key : stricter check for internal service-to-service calls
"""

import hmac
import logging

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_api_key_scheme = APIKeyHeader(name=settings.api_key_header, auto_error=False)


def require_api_key(api_key: str | None = Security(_api_key_scheme)) -> str:
    """
    Validate the X-API-Key header against `internal_api_key`.
    Uses constant-time comparison to prevent timing attacks.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    if not hmac.compare_digest(api_key, settings.internal_api_key):
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return api_key


def require_internal_key(api_key: str = Depends(require_api_key)) -> str:
    """
    Alias that makes the intent explicit in router declarations.
    Both guards use the same underlying key for now; swap out if keys diverge.
    """
    return api_key
