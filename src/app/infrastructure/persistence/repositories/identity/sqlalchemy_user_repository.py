from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .....application.identity.exceptions import UserAlreadyExists
from .....application.identity.interfaces.user_repository import UserRepository
from .....domain.identity.entities.session import Session as SessionEntity
from .....domain.identity.entities.user import User as UserEntity
from .....domain.identity.value_objects.email import EmailAddress
from ...models.identity.session import Session
from ...models.identity.user import User


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
        self._session.add_all([user_model, session_model])
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
