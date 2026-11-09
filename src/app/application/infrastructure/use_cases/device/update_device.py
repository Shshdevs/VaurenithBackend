from datetime import UTC, datetime
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceData
from app.application.infrastructure.exceptions import DeviceNotFound, DeviceVersionConflict
from app.application.infrastructure.interfaces import DeviceRepository
from app.application.infrastructure.use_cases.device.operating_system import (
    build_operating_system_info,
)
from app.domain.infrastructure import Device, DeviceName, InvalidDevice
from app.domain.infrastructure.enums import DeviceType


class UpdateDevice:
    def __init__(self, device_repository: DeviceRepository) -> None:
        self._device_repository = device_repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        device_id: UUID,
        expected_version: int,
        name: str,
        device_type: DeviceType,
        hostname: str | None = None,
        description: str | None = None,
        operating_system: str | None = None,
        os_version: str | None = None,
        architecture: str | None = None,
        tags: list[str] | None = None,
    ) -> DeviceData:
        existing = await self._device_repository.get_by_id(identity, device_id)
        if existing is None:
            raise DeviceNotFound(str(device_id))
        if existing.version != expected_version:
            raise DeviceVersionConflict(expected_version, existing.version)

        try:
            device = Device(
                entity_id=existing.id,
                user_id=existing.user_id,
                name=DeviceName(name),
                created_at=existing.created_at,
                updated_at=datetime.now(UTC),
                device_type=device_type,
                hostname=hostname,
                description=description,
                operating_system_info=build_operating_system_info(
                    operating_system, os_version, architecture
                ),
                tags=tags,
                version=expected_version + 1,
                last_seen_at=existing.last_seen_at,
                last_status_at=existing.last_status_at,
            )
        except InvalidDevice as error:
            raise InvalidInput(str(error)) from error

        if not await self._device_repository.update(identity, device, expected_version):
            latest = await self._device_repository.get_by_id(identity, device_id)
            if latest is None:
                raise DeviceNotFound(str(device_id))
            raise DeviceVersionConflict(expected_version, latest.version)
        return DeviceData.from_device(device)
