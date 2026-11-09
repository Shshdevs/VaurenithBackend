from datetime import UTC, datetime
from uuid import uuid4

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceData
from app.application.infrastructure.interfaces import DeviceRepository
from app.application.infrastructure.use_cases.device.operating_system import (
    build_operating_system_info,
)
from app.domain.infrastructure import Device, DeviceName, InvalidDevice
from app.domain.infrastructure.enums import DeviceType


class CreateDevice:
    def __init__(self, device_repository: DeviceRepository) -> None:
        self._device_repository = device_repository

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
        return DeviceData.from_device(device)
