from datetime import UTC, datetime
from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity.dto import ClientDeviceData, VerifiedIdentity
from app.application.identity.exceptions import (
    ClientDeviceConflict,
    ClientDeviceNotFound,
)
from app.application.identity.interfaces import (
    ClientDeviceRepository,
    SessionRepository,
)
from app.domain.identity import ClientDeviceStatus


class SetClientDeviceStatus:
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
    async def execute(
        self,
        identity: VerifiedIdentity,
        device_id: UUID,
        target_status: ClientDeviceStatus,
    ) -> ClientDeviceData:
        if target_status is ClientDeviceStatus.REVOKED:
            raise ClientDeviceConflict("A revoked status is terminal")
        device = await self._client_device_repository.get_owned(
            identity.user_id, device_id, for_update=True
        )
        if device is None:
            raise ClientDeviceNotFound()

        if target_status is ClientDeviceStatus.INACTIVE:
            if device.status is ClientDeviceStatus.REVOKED:
                raise ClientDeviceConflict("A revoked device cannot be reactivated")
            device.deactivate()
            await self._session_repository.revoke_device_sessions(
                identity.user_id, device.id, datetime.now(UTC)
            )
        else:
            if device.status is ClientDeviceStatus.REVOKED:
                raise ClientDeviceConflict("A revoked device cannot be reactivated")
            device.activate()

        await self._client_device_repository.save(device)
        return ClientDeviceData.from_entity(device)
