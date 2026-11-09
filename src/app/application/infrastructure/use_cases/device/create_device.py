from datetime import UTC, datetime
from uuid import uuid4

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceData
from app.application.infrastructure.interfaces import DeviceRepository
from app.application.infrastructure.use_cases.device.operating_system import (
    build_operating_system_info,
)
from app.application.synchronization.change_log.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import Device, DeviceName, InvalidDevice
from app.domain.infrastructure.enums import DeviceType
from app.domain.synchronization import ChangeOperation


class CreateDevice:
    def __init__(
        self, device_repository: DeviceRepository, recorder: ChangeRecorder
    ) -> None:
        self._device_repository = device_repository
        self._recorder = recorder

    async def execute(
        self,
        identity: VerifiedIdentity,
        name: str,
        device_type: DeviceType,
        hostname: str | None = None,
        description: str | None = None,
        operating_system: str | None = None,
        os_version: str | None = None,
        architecture: str | None = None,
        tags: list[str] | None = None,
    ) -> DeviceData:
        now = datetime.now(UTC)
        try:
            device = Device(
                entity_id=uuid4(),
                user_id=identity.user_id,
                name=DeviceName(name),
                created_at=now,
                updated_at=now,
                device_type=device_type,
                hostname=hostname,
                description=description,
                operating_system_info=build_operating_system_info(
                    operating_system, os_version, architecture
                ),
                tags=tags,
            )
        except InvalidDevice as error:
            raise InvalidInput(str(error)) from error

        await self._device_repository.create(device)
        await self._recorder.execute(
            identity,
            EntityType.DEVICE,
            device.id,
            ChangeOperation.INSERT,
            device.version,
            {
                "name": device.name,
                "hostname": device.hostname,
                "description": device.description,
                "device_type": device.device_type.value,
                "operating_system": device.operating_system,
                "os_version": device.os_version,
                "architecture": device.architecture,
                "tags": device.tags,
            },
        )
        return DeviceData.from_device(device)
