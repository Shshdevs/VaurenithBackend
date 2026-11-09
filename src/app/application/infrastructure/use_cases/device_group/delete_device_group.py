from uuid import UUID

from app.application.identity.dto import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceGroupNotFound
from app.application.infrastructure.interfaces import DeviceGroupRepository


class DeleteDeviceGroup:
    def __init__(self, device_group_repository: DeviceGroupRepository) -> None:
        self._device_group_repository = device_group_repository

    async def execute(self, identity: VerifiedIdentity, device_group_id: UUID) -> None:
        result = await self._device_group_repository.delete(
            identity=identity, device_group_id=device_group_id
        )

        if not result:
            raise DeviceGroupNotFound(str(device_group_id))
