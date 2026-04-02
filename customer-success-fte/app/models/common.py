"""
Shared Pydantic types used across all routers and services.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard envelope for all API responses."""

    success: bool = True
    data: DataT | None = None
    message: str = "OK"


class ErrorDetail(BaseModel):
    """Structured error payload returned on 4xx/5xx."""

    code: str
    message: str
    detail: Any | None = None
