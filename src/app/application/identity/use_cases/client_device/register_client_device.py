from datetime import UTC, datetime
from uuid import uuid4

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity.dto import ClientDeviceData, VerifiedIdentity
from app.application.identity.exceptions import (
    ClientDeviceConflict,
    UserNotFound,
)
from app.application.identity.interfaces import (
    ClientDeviceRepository,
    SessionRepository,
    UserRepository,
)
from app.domain.identity import ClientDevice, PlatformType, Session


class RegisterClientDevice:
    def __init__(
        self,
        user_repository: UserRepository,
        client_device_repository: ClientDeviceRepository,
        session_repository: SessionRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._user_repository = user_repository
        self._client_device_repository = client_device_repository
        self._session_repository = session_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(
        self,
        identity: VerifiedIdentity,
        name: str,
        platform: PlatformType,
        app_version: str | None,
    ) -> ClientDeviceData:
        if await self._user_repository.get_by_id(identity.user_id) is None:
            raise UserNotFound(identity.user_id)
        if await self._session_repository.has_token_hash(identity.token_hash):
            raise ClientDeviceConflict("Identity token has already been registered")

        now = datetime.now(UTC)
        device = ClientDevice(
            entity_id=uuid4(),
            user_id=identity.user_id,
            name=name,
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
            client_device_id=device.id,
        )
        await self._client_device_repository.create(device)
        await self._session_repository.create(session)
        return ClientDeviceData.from_entity(device)
