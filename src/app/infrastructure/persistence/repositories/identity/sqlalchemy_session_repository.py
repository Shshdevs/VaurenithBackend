from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.interfaces import SessionRepository
from app.domain.identity.value_objects.token_hash import TokenHash
from app.infrastructure.persistence.models.identity.session import Session


class SqlAlchemySessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_active_session(self, token_hash: TokenHash, at: datetime) -> bool:
        statement = select(Session.id).where(
            Session.token_hash == token_hash.value,
            Session.revoked_at.is_(None),
            Session.expires_at > at,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None
