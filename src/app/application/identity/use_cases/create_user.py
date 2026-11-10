from datetime import UTC, datetime
from uuid import uuid4

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity.dto import UserData, VerifiedIdentity
from app.application.identity.exceptions import InvalidIdentity
from app.application.identity.interfaces import UserRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.identity import (
    ClientDevice,
    EmailAddress,
    InvalidEmail,
    PlatformType,
    Session,
    User,
)
from app.domain.synchronization import ChangeOperation


class CreateUser:
    def __init__(
        self,
        user_repository: UserRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._user_repository = user_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(
        self,
        identity: VerifiedIdentity,
        email: str,
        display_name: str | None,
        device_name: str,
        platform: PlatformType,
        app_version: str | None,
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
        client_device = ClientDevice(
            entity_id=uuid4(),
            user_id=identity.user_id,
            name=device_name,
            platform=platform,
            app_version=app_version,
            registered_at=now,
            last_seen_at=now,
        )
        session = Session(
            entity_id=uuid4(),
            user_id=identity.user_id,
            token_hash=identity.token_hash,
            expires_at=identity.expires_at,
            created_at=now,
            client_device_id=client_device.id,
        )
        await self._user_repository.register(user, client_device, session)
        await self._recorder.execute(
            identity,
            EntityType.USER,
            user.id,
            ChangeOperation.INSERT,
            1,
        )

        return UserData(
            id=user.id,
            email=str(user.email),
            display_name=user.display_name,
            nickname=user.nickname,
            auth_provider=user.auth_provider,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
