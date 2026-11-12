from datetime import UTC, datetime
from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity.dto import VerifiedIdentity
from app.application.identity.exceptions import ClientDeviceNotFound
from app.application.identity.interfaces import (
    ClientDeviceRepository,
    SessionRepository,
)


class RevokeClientDevice:
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
    async def execute(self, identity: VerifiedIdentity, device_id: UUID) -> None:
        device = await self._client_device_repository.get_owned(
            identity.user_id, device_id, for_update=True
        )
        if device is None:
            raise ClientDeviceNotFound()
        now = datetime.now(UTC)
        device.revoke(now)
        await self._session_repository.revoke_device_sessions(
            identity.user_id, device.id, now
        )
        await self._client_device_repository.save(device)
