from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceData
from app.application.infrastructure.interfaces import DeviceRepository


class GetUserDevices:
    def __init__(self, device_repository: DeviceRepository) -> None:
        self._device_repository = device_repository

    async def execute(self, identity: VerifiedIdentity) -> list[DeviceData]:
        devices = await self._device_repository.get_by_user(identity)
        return [DeviceData.from_device(device) for device in devices]
