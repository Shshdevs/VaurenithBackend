from datetime import UTC, datetime
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceGroupData
from app.application.infrastructure.exceptions import (
    DeviceGroupNotFound,
    DeviceGroupVersionConflict,
)
from app.application.infrastructure.interfaces import DeviceGroupRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import DeviceGroup, DeviceGroupName, InvalidDeviceGroup
from app.domain.synchronization import ChangeOperation


class UpdateDeviceGroup:
    def __init__(
        self,
        device_group_repository: DeviceGroupRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._device_group_repository = device_group_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(
        self,
        device_group_id: UUID,
        identity: VerifiedIdentity,
        name: str,
        description: str | None,
        expected_version: int,
    ) -> DeviceGroupData:
        existing_device_group = await self._device_group_repository.get_by_id(
            device_group_id=device_group_id, identity=identity
        )
        if not existing_device_group:
            raise DeviceGroupNotFound(str(device_group_id))

        try:
            now = datetime.now(UTC)
            device_group = DeviceGroup(
                entity_id=existing_device_group.id,
                user_id=existing_device_group.user_id,
                name=DeviceGroupName(name),
                description=description,
                created_at=existing_device_group.created_at,
                updated_at=now,
                version=existing_device_group.version + 1,
            )
        except InvalidDeviceGroup as error:
            raise InvalidInput(str(error)) from error

        updated_version = await self._device_group_repository.update(
            device_group=device_group, identity=identity, expected_version=expected_version
        )
        if updated_version is None:
            current = await self._device_group_repository.get_by_id(
                device_group_id=device_group_id, identity=identity
            )
            if current is None:
                raise DeviceGroupNotFound(str(device_group_id))
            if current.version == expected_version:
                raise DeviceGroupNotFound(str(device_group_id))
            raise DeviceGroupVersionConflict(expected_version, current.version)
        device_group = DeviceGroup(
            entity_id=device_group.id,
            user_id=device_group.user_id,
            name=device_group.name_value,
            description=device_group.description,
            created_at=device_group.created_at,
            updated_at=device_group.updated_at,
            version=updated_version,
        )
        await self._recorder.execute(
            identity,
            EntityType.DEVICE_GROUP,
            device_group.id,
            ChangeOperation.UPDATE,
            device_group.version,
            {"name": device_group.name, "description": device_group.description},
        )

        return DeviceGroupData.from_device_group(device_group=device_group)
