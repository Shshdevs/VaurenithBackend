from datetime import UTC, datetime
from uuid import uuid4

from ....domain.identity.entities.session import Session
from ....domain.identity.entities.user import User
from ....domain.identity.exceptions import InvalidEmail
from ....domain.identity.value_objects.email import EmailAddress
from ..dto.user_data import UserData
from ..dto.verified_identity import VerifiedIdentity
from ..exceptions import InvalidIdentity
from ..interfaces.user_repository import UserRepository


class CreateUser:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        email: str,
        display_name: str | None,
    ) -> UserData:
        try:
            email_address = EmailAddress(email)
        except InvalidEmail as error:
            raise InvalidIdentity("Email does not match verified identity") from error
        if email_address != identity.email:
            raise InvalidIdentity("Email does not match verified identity")

        now = datetime.now(UTC)
        user = User(
            entity_id=identity.user_id,
            email=email_address,
            display_name=display_name,
            auth_provider=identity.auth_provider,
            created_at=now,
            updated_at=now,
        )
        session = Session(
            entity_id=uuid4(),
            user_id=identity.user_id,
            token_hash=identity.token_hash,
            expires_at=identity.expires_at,
            created_at=now,
        )
        await self._user_repository.register(user, session)

        return UserData(
            id=user.id,
            email=str(user.email),
            display_name=user.display_name,
            auth_provider=user.auth_provider,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
