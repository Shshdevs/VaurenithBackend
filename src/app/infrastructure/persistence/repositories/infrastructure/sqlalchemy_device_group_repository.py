from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import (
    DeviceGroupAlreadyExists,
    DeviceGroupDeletionConflict,
)
from app.application.infrastructure.interfaces import DeviceGroupRepository
from app.domain.infrastructure import DeviceGroup as DeviceGroupEntity
from app.domain.infrastructure import DeviceGroupName
from app.infrastructure.persistence.models import DeviceGroup


class SqlAlchemyDeviceGroupRepository(DeviceGroupRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, identity: VerifiedIdentity, device_group_id: UUID
    ) -> DeviceGroupEntity | None:
        result = await self._session.execute(
            select(DeviceGroup).where(
                DeviceGroup.id == device_group_id, DeviceGroup.user_id == identity.user_id
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, device_group: DeviceGroupEntity) -> None:
        self._session.add(self._to_model(device_group))

        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            if getattr(error.orig, "sqlstate", None) == "23505":
                raise DeviceGroupAlreadyExists(device_group.name) from error
            raise

    async def update(
        self, identity: VerifiedIdentity, device_group: DeviceGroupEntity
    ) -> bool:
        statement = (
            update(DeviceGroup)
            .where(
                DeviceGroup.id == device_group.id, DeviceGroup.user_id == identity.user_id
            )
            .values(
                user_id=device_group.user_id,
                name=device_group.name,
                description=device_group.description,
                updated_at=device_group.updated_at,
            )
            .returning(DeviceGroup.id)
        )

        try:
            result = await self._session.execute(statement)
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            if getattr(error.orig, "sqlstate", None) == "23505":
                raise DeviceGroupAlreadyExists(device_group.name) from error
            raise

        return result.scalar_one_or_none() is not None

    async def delete(self, identity: VerifiedIdentity, device_group_id: UUID) -> bool:
        statement = (
            delete(DeviceGroup)
            .where(
                DeviceGroup.id == device_group_id, DeviceGroup.user_id == identity.user_id
            )
            .returning(DeviceGroup.id)
        )
        try:
            result = await self._session.execute(statement)
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            if getattr(error.orig, "sqlstate", None) == "23503":
                raise DeviceGroupDeletionConflict(str(device_group_id)) from error
            raise

        return result.scalar_one_or_none() is not None

    def _to_entity(self, model: DeviceGroup) -> DeviceGroupEntity:
        return DeviceGroupEntity(
            entity_id=model.id,
            user_id=model.user_id,
            name=DeviceGroupName(model.name),
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: DeviceGroupEntity) -> DeviceGroup:
        return DeviceGroup(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
