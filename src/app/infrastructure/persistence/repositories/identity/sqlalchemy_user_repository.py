from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.exceptions import UserAlreadyExists
from app.application.identity.interfaces import UserRepository
from app.domain.identity import ClientDevice as ClientDeviceEntity
from app.domain.identity import EmailAddress
from app.domain.identity.entities.session import Session as SessionEntity
from app.domain.identity.entities.user import User as UserEntity
from app.infrastructure.persistence.models.identity.client_device import ClientDevice
from app.infrastructure.persistence.models.identity.session import Session
from app.infrastructure.persistence.models.identity.user import User


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> UserEntity | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def register(
        self,
        user: UserEntity,
        client_device: ClientDeviceEntity,
        session: SessionEntity,
    ) -> None:
        user_model = User(
            id=user.id,
            email=user.email.value,
            display_name=user.display_name,
            auth_provider=user.auth_provider,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        session_model = Session(
            id=session.id,
            user_id=session.user_id,
            client_device_id=session.client_device_id,
            token_hash=session.token_hash.value,
            expires_at=session.expires_at,
            created_at=session.created_at,
            revoked_at=session.revoked_at,
        )
        client_device_model = ClientDevice(
            id=client_device.id,
            user_id=client_device.user_id,
            name=client_device.name,
            platform=client_device.platform,
            app_version=client_device.app_version,
            status=client_device.status,
            registered_at=client_device.registered_at,
            last_seen_at=client_device.last_seen_at,
            revoked_at=client_device.revoked_at,
        )
        client_device_model.user = user_model
        session_model.user = user_model
        session_model.client_device = client_device_model
        self._session.add_all([user_model, client_device_model, session_model])
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise UserAlreadyExists(str(user.email)) from error

    @staticmethod
    def _to_entity(model: User) -> UserEntity:
        return UserEntity(
            entity_id=model.id,
            email=EmailAddress(model.email),
            display_name=model.display_name,
            auth_provider=model.auth_provider,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
