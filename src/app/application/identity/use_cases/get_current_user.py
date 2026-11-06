from uuid import UUID

from app.application.identity.dto import UserData
from app.application.identity.exceptions import UserNotFound
from app.application.identity.interfaces import UserRepository


class GetCurrentUser:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, user_id: UUID) -> UserData:
        user = await self._user_repository.get_by_id(user_id)

        if not user:
            raise UserNotFound(user_id=user_id)

        return UserData(
            id=user.id,
            email=str(user.email),
            display_name=user.display_name,
            auth_provider=user.auth_provider,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
