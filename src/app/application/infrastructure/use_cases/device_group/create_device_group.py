from datetime import UTC, datetime
from uuid import uuid4

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceGroupData
from app.application.infrastructure.interfaces import DeviceGroupRepository
from app.domain.infrastructure import DeviceGroup, DeviceGroupName, InvalidDeviceGroup


class CreateDeviceGroup:
    def __init__(self, device_group_repository: DeviceGroupRepository) -> None:
        self._device_group_repository = device_group_repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        name: str,
        description: str | None,
    ) -> DeviceGroupData:
        try:
            device_group_name = DeviceGroupName(name)
            now = datetime.now(UTC)
            device_group = DeviceGroup(
                entity_id=uuid4(),
                user_id=identity.user_id,
                description=description,
                name=device_group_name,
                created_at=now,
                updated_at=now,
            )
        except InvalidDeviceGroup as error:
            raise InvalidInput(str(error)) from error

        await self._device_group_repository.create(device_group=device_group)

        return DeviceGroupData.from_device_group(device_group=device_group)
