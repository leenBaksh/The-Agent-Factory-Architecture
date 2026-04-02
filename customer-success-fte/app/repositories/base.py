"""
Generic async repository providing standard CRUD operations.
All table-specific repositories extend this class.
"""

import uuid
from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic CRUD repository.

    Usage:
        class CustomerRepository(BaseRepository[Customer]):
            model = Customer
    """

    model: Type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get(self, id: uuid.UUID) -> ModelT | None:
        """Fetch a single record by primary key."""
        return await self.session.get(self.model, id)

    async def get_or_raise(self, id: uuid.UUID) -> ModelT:
        """Fetch a single record by primary key; raise ValueError if not found."""
        obj = await self.session.get(self.model, id)
        if obj is None:
            raise ValueError(f"{self.model.__name__} {id} not found")
        return obj

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ModelT]:
        """Return all rows with pagination."""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return result.scalars().all()

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(self, **kwargs: Any) -> ModelT:
        """Instantiate, persist, and flush a new record."""
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelT, **kwargs: Any) -> ModelT:
        """Apply keyword updates to an existing ORM object and flush."""
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj
