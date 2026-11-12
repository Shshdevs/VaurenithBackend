from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.exceptions import SessionTokenConflict
from app.application.identity.interfaces import SessionRepository
from app.domain.identity import ClientDeviceStatus
from app.domain.identity import Session as SessionEntity
from app.domain.identity.value_objects.token_hash import TokenHash
from app.infrastructure.persistence.models.identity.client_device import ClientDevice
from app.infrastructure.persistence.models.identity.session import Session as SessionModel


class SqlAlchemySessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_active_session(
        self, user_id: UUID, token_hash: TokenHash, at: datetime
    ) -> bool:
        statement = (
            select(SessionModel.id)
            .join(
                ClientDevice,
                and_(
                    ClientDevice.id == SessionModel.client_device_id,
                    ClientDevice.user_id == SessionModel.user_id,
                ),
            )
            .where(
                SessionModel.user_id == user_id,
                SessionModel.token_hash == token_hash.value,
                SessionModel.revoked_at.is_(None),
                SessionModel.expires_at > at,
                ClientDevice.status == ClientDeviceStatus.ACTIVE,
            )
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def has_token_hash(self, token_hash: TokenHash) -> bool:
        result = await self._session.execute(
            select(SessionModel.id).where(SessionModel.token_hash == token_hash.value)
        )
        return result.scalar_one_or_none() is not None

    async def create(self, session: SessionEntity) -> None:
        self._session.add(
            SessionModel(
                id=session.id,
                user_id=session.user_id,
                client_device_id=session.client_device_id,
                token_hash=session.token_hash.value,
                expires_at=session.expires_at,
                created_at=session.created_at,
                revoked_at=session.revoked_at,
            )
        )
        try:
            await self._session.flush()
        except IntegrityError as error:
            diagnostic = getattr(error.orig, "diag", None)
            constraint_name = getattr(diagnostic, "constraint_name", None)
            if constraint_name == "uq_sessions_token_hash":
                raise SessionTokenConflict() from error
            raise

    async def revoke_device_sessions(
        self, user_id: UUID, client_device_id: UUID, at: datetime
    ) -> int:
        statement = (
            update(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.client_device_id == client_device_id,
                SessionModel.revoked_at.is_(None),
                SessionModel.expires_at > at,
            )
            .values(revoked_at=at)
            .returning(SessionModel.id)
        )
        result = await self._session.execute(statement)
        return len(result.scalars().all())

    async def list_device_sessions(
        self, user_id: UUID, client_device_id: UUID
    ) -> list[SessionEntity]:
        result = await self._session.execute(
            select(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.client_device_id == client_device_id,
            )
            .order_by(SessionModel.created_at.desc(), SessionModel.id)
        )
        return [self._to_entity(model) for model in result.scalars()]

    async def revoke_session(self, token_hash: TokenHash, at: datetime) -> bool:
        statement = (
            update(SessionModel)
            .where(
                SessionModel.token_hash == token_hash.value,
                SessionModel.revoked_at.is_(None),
                SessionModel.expires_at > at,
            )
            .values(revoked_at=at)
            .returning(SessionModel.id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _to_entity(model: SessionModel) -> SessionEntity:
        return SessionEntity(
            entity_id=model.id,
            user_id=model.user_id,
            client_device_id=model.client_device_id,
            token_hash=TokenHash(model.token_hash),
            expires_at=model.expires_at,
            created_at=model.created_at,
            revoked_at=model.revoked_at,
        )
