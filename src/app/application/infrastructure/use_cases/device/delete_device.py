from datetime import UTC, datetime
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceNotFound
from app.application.infrastructure.interfaces import DeviceRepository


class DeleteDevice:
    def __init__(self, device_repository: DeviceRepository) -> None:
        self._device_repository = device_repository

    async def execute(self, identity: VerifiedIdentity, device_id: UUID) -> None:
        deleted = await self._device_repository.delete(
            identity, device_id, datetime.now(UTC)
        )
        if not deleted:
            raise DeviceNotFound(str(device_id))
