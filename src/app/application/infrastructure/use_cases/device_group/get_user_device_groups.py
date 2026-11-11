from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceGroupData
from app.application.infrastructure.interfaces import DeviceGroupRepository


class GetUserDeviceGroups:
    def __init__(self, device_group_repository: DeviceGroupRepository) -> None:
        self._device_group_repository = device_group_repository

    async def execute(self, identity: VerifiedIdentity) -> list[DeviceGroupData]:
        groups = await self._device_group_repository.get_by_user(identity)
        return [DeviceGroupData.from_device_group(group) for group in groups]
