from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Exists

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.interfaces import DeviceRepository
from app.domain.infrastructure import Device as DeviceEntity
from app.domain.infrastructure import DeviceName, OperatingSystem
from app.infrastructure.persistence.models import Device as DeviceModel


class SqlAlchemyDeviceRepository(DeviceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> DeviceEntity | None:
        result = await self._session.execute(
            select(DeviceModel).where(self._owned_active_device(identity, device_id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_by_user(self, identity: VerifiedIdentity) -> list[DeviceEntity]:
        result = await self._session.execute(
            select(DeviceModel)
            .where(
                DeviceModel.user_id == identity.user_id,
                DeviceModel.deleted_at.is_(None),
            )
            .order_by(DeviceModel.created_at, DeviceModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def create(self, device: DeviceEntity) -> None:
        self._session.add(self._to_model(device))

    async def update(
        self, identity: VerifiedIdentity, device: DeviceEntity, expected_version: int
    ) -> bool:
        result = await self._session.execute(
            update(DeviceModel)
            .where(
                self._owned_active_device(identity, device.id),
                DeviceModel.version == expected_version,
            )
            .values(
                name=device.name,
                hostname=device.hostname,
                description=device.description,
                device_type=device.device_type,
                operating_system=device.operating_system,
                os_version=device.os_version,
                architecture=device.architecture,
                tags=device.tags,
                version=expected_version + 1,
                updated_at=device.updated_at,
            )
            .returning(DeviceModel.id)
        )
        updated_id = result.scalar_one_or_none()
        return updated_id is not None

    async def delete(
        self, identity: VerifiedIdentity, device_id: UUID, deleted_at: datetime
    ) -> bool:
        result = await self._session.execute(
            update(DeviceModel)
            .where(self._owned_active_device(identity, device_id))
            .values(
                deleted_at=deleted_at,
                updated_at=deleted_at,
                version=DeviceModel.version + 1,
            )
            .returning(DeviceModel.version)
        )
        deleted_version = result.scalar_one_or_none()
        return deleted_version is not None

    @staticmethod
    def _owned_active_device(identity: VerifiedIdentity, device_id: UUID) -> Exists:
        return exists(
            select(DeviceModel.id).where(
                DeviceModel.id == device_id,
                DeviceModel.user_id == identity.user_id,
                DeviceModel.deleted_at.is_(None),
            )
        )

    @staticmethod
    def _to_entity(model: DeviceModel) -> DeviceEntity:
        operating_system_info = None
        if any(
            value is not None and value.strip()
            for value in (model.operating_system, model.os_version, model.architecture)
        ):
            operating_system_info = OperatingSystem(
                name=model.operating_system,
                version=model.os_version,
                architecture=model.architecture,
            )
        return DeviceEntity(
            entity_id=model.id,
            user_id=model.user_id,
            name=DeviceName(model.name),
            created_at=model.created_at,
            updated_at=model.updated_at,
            device_type=model.device_type,
            hostname=model.hostname,
            description=model.description,
            operating_system_info=operating_system_info,
            tags=model.tags,
            version=model.version,
            last_seen_at=model.last_seen_at,
            last_status_at=model.last_status_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _to_model(device: DeviceEntity) -> DeviceModel:
        return DeviceModel(
            id=device.id,
            user_id=device.user_id,
            name=device.name,
            slug=device.slug,
            hostname=device.hostname,
            description=device.description,
            device_type=device.device_type,
            operating_system=device.operating_system,
            os_version=device.os_version,
            architecture=device.architecture,
            tags=device.tags,
            last_seen_at=device.last_seen_at,
            last_status_at=device.last_status_at,
            version=device.version,
            created_at=device.created_at,
            updated_at=device.updated_at,
            deleted_at=device.deleted_at,
        )
