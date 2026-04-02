"""Repository for the customers table."""

from typing import Sequence

from sqlalchemy import select

from app.database import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    async def get_by_email(self, email: str) -> Customer | None:
        result = await self.session.execute(
            select(Customer).where(Customer.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Customer | None:
        result = await self.session.execute(
            select(Customer).where(Customer.phone == phone)
        )
        return result.scalar_one_or_none()

    async def search_by_company(self, company: str) -> Sequence[Customer]:
        result = await self.session.execute(
            select(Customer).where(Customer.company.ilike(f"%{company}%"))
        )
        return result.scalars().all()
