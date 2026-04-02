"""Repository for the knowledge_base table."""

from typing import Sequence

from sqlalchemy import select, text

from app.database import KnowledgeBase
from app.repositories.base import BaseRepository


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    model = KnowledgeBase

    async def list_active(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[KnowledgeBase]:
        result = await self.session.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.is_active.is_(True))
            .order_by(KnowledgeBase.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def list_by_category(self, category: str) -> Sequence[KnowledgeBase]:
        result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.category == category,
                KnowledgeBase.is_active.is_(True),
            )
        )
        return result.scalars().all()

    async def semantic_search(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
        min_score: float = 0.7,
    ) -> Sequence[KnowledgeBase]:
        """
        Cosine-similarity search using pgvector.
        Returns up to `limit` active articles ordered by similarity desc.
        """
        result = await self.session.execute(
            text(
                """
                SELECT kb.*,
                       1 - (kb.embedding <=> CAST(:embedding AS vector)) AS score
                FROM   knowledge_base kb
                WHERE  kb.is_active = TRUE
                  AND  kb.embedding IS NOT NULL
                  AND  1 - (kb.embedding <=> CAST(:embedding AS vector)) >= :min_score
                ORDER  BY kb.embedding <=> CAST(:embedding AS vector)
                LIMIT  :limit
                """
            ),
            {
                "embedding": str(embedding),
                "min_score": min_score,
                "limit": limit,
            },
        )
        rows = result.mappings().all()
        return [KnowledgeBase(**{k: v for k, v in row.items() if k != "score"}) for row in rows]
