from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceGroupData
from app.application.infrastructure.exceptions import DeviceGroupNotFound
from app.application.infrastructure.interfaces import DeviceGroupRepository


class GetDeviceGroup:
    def __init__(self, device_group_repository: DeviceGroupRepository) -> None:
        self._device_group_repository = device_group_repository

    async def execute(
        self, identity: VerifiedIdentity, device_group_id: UUID
    ) -> DeviceGroupData:
        result = await self._device_group_repository.get_by_id(
            device_group_id=device_group_id, identity=identity
        )

        if not result:
            raise DeviceGroupNotFound(str(device_group_id))
        return DeviceGroupData.from_device_group(result)
