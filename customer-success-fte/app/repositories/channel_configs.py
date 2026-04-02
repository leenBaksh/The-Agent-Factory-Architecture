"""Repository for the channel_configs table."""

from sqlalchemy import select

from app.database import ChannelConfig, ChannelType
from app.repositories.base import BaseRepository


class ChannelConfigRepository(BaseRepository[ChannelConfig]):
    model = ChannelConfig

    async def get_by_channel(self, channel: ChannelType) -> ChannelConfig | None:
        result = await self.session.execute(
            select(ChannelConfig).where(ChannelConfig.channel == channel)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[ChannelConfig]:
        result = await self.session.execute(
            select(ChannelConfig).where(ChannelConfig.is_active.is_(True))
        )
        return list(result.scalars().all())
