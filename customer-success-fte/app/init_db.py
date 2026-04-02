"""
Database initialisation script.

Run once on first deploy (or in CI) to:
  1. Enable required PostgreSQL extensions (pgvector, pgcrypto)
  2. Create all ORM-mapped tables

Usage:
    python -m app.init_db
"""

import asyncio
import logging

from sqlalchemy import text

from app.database import Base, engine

logger = logging.getLogger(__name__)


async def init_extensions() -> None:
    """Enable pgcrypto and pgvector extensions if not already present."""
    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "vector"'))
        logger.info("PostgreSQL extensions ready.")


async def create_tables() -> None:
    """Create all tables defined in the ORM models."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created (or already exist).")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Initialising database …")
    await init_extensions()
    await create_tables()
    await engine.dispose()
    logger.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
