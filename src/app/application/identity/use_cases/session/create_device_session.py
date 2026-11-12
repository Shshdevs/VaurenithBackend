from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity.dto import SessionData, VerifiedIdentity
from app.application.identity.exceptions import (
    ClientDeviceConflict,
    ClientDeviceNotFound,
    SessionTokenConflict,
)
from app.application.identity.interfaces import (
    ClientDeviceRepository,
    SessionRepository,
)
from app.domain.identity import ClientDeviceStatus, Session


class CreateDeviceSession:
    def __init__(
        self,
        client_device_repository: ClientDeviceRepository,
        session_repository: SessionRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._client_device_repository = client_device_repository
        self._session_repository = session_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(self, identity: VerifiedIdentity, device_id: UUID) -> SessionData:
        if await self._session_repository.has_token_hash(identity.token_hash):
            raise SessionTokenConflict()
        device = await self._client_device_repository.get_owned(
            identity.user_id, device_id, for_update=True
        )
        if device is None:
            raise ClientDeviceNotFound()
        if device.status is not ClientDeviceStatus.ACTIVE:
            raise ClientDeviceConflict()

        now = datetime.now(UTC)
        device.mark_seen(now)
        session = Session(
            entity_id=uuid4(),
            user_id=identity.user_id,
            token_hash=identity.token_hash,
            expires_at=identity.expires_at,
            created_at=now,
            client_device_id=device.id,
        )
        await self._client_device_repository.save(device)
        await self._session_repository.create(session)
        return SessionData.from_entity(session)
