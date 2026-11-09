from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceData
from app.application.infrastructure.exceptions import DeviceNotFound
from app.application.infrastructure.interfaces import DeviceRepository


class GetDevice:
    def __init__(self, device_repository: DeviceRepository) -> None:
        self._device_repository = device_repository

    async def execute(self, identity: VerifiedIdentity, device_id: UUID) -> DeviceData:
        device = await self._device_repository.get_by_id(identity, device_id)
        if device is None:
            raise DeviceNotFound(str(device_id))
        return DeviceData.from_device(device)
