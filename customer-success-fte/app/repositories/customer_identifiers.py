"""Repository for the customer_identifiers table."""

import uuid

from sqlalchemy import select

from app.database import ChannelType, CustomerIdentifier
from app.repositories.base import BaseRepository


class CustomerIdentifierRepository(BaseRepository[CustomerIdentifier]):
    model = CustomerIdentifier

    async def get_by_channel_and_external_id(
        self,
        channel: ChannelType,
        external_id: str,
    ) -> CustomerIdentifier | None:
        """Primary lookup: resolve a channel identity to a customer record."""
        result = await self.session.execute(
            select(CustomerIdentifier).where(
                CustomerIdentifier.channel == channel,
                CustomerIdentifier.external_id == external_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_customer(
        self, customer_id: uuid.UUID
    ) -> list[CustomerIdentifier]:
        result = await self.session.execute(
            select(CustomerIdentifier).where(
                CustomerIdentifier.customer_id == customer_id
            )
        )
        return list(result.scalars().all())
