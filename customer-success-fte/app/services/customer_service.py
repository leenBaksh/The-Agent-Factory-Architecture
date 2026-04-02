"""
Customer resolution service.

Resolves or creates a Customer from a channel identity.
Single entry point for all channel adapters — keeps identity logic centralised.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import ChannelType, Customer, CustomerIdentifier
from app.repositories.customer_identifiers import CustomerIdentifierRepository
from app.repositories.customers import CustomerRepository

logger = logging.getLogger(__name__)


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self._customers = CustomerRepository(session)
        self._identifiers = CustomerIdentifierRepository(session)

    async def resolve_or_create(
        self,
        *,
        channel: ChannelType,
        external_id: str,
        display_name: str,
        email: str | None = None,
        phone: str | None = None,
        company: str | None = None,
    ) -> Customer:
        """
        Look up a customer by their channel identity.
        If no identity record exists, create the customer and link the identity.

        Returns the resolved or newly created Customer ORM object.
        """
        identifier = await self._identifiers.get_by_channel_and_external_id(
            channel, external_id
        )

        if identifier is not None:
            customer = await self._customers.get_or_raise(identifier.customer_id)
            logger.debug(
                "Resolved existing customer %s via %s/%s",
                customer.id,
                channel,
                external_id,
            )
            return customer

        # No existing identity — try to match by email/phone before creating
        customer = None
        if email:
            customer = await self._customers.get_by_email(email)
        if customer is None and phone:
            customer = await self._customers.get_by_phone(phone)

        if customer is None:
            customer = await self._customers.create(
                display_name=display_name,
                email=email,
                phone=phone,
                company=company,
            )
            logger.info("Created new customer %s.", customer.id)

        await self._identifiers.create(
            customer_id=customer.id,
            channel=channel,
            external_id=external_id,
        )
        logger.info(
            "Linked %s/%s to customer %s.", channel, external_id, customer.id
        )
        return customer
