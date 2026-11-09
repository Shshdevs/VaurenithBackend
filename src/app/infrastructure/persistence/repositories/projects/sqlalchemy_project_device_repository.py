from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.exceptions import ProjectDeviceDeletionConflict
from app.application.projects.interfaces import ProjectDeviceRepository
from app.domain.projects import ProjectDevice as ProjectDeviceEntity
from app.domain.projects import ProjectDeviceRole
from app.infrastructure.persistence.models import ProjectDevice


class SqlAlchemyProjectDeviceRepository(ProjectDeviceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_device_id: UUID) -> ProjectDeviceEntity | None:
        result = await self._session.execute(
            select(ProjectDevice).where(ProjectDevice.id == project_device_id)
        )
        project_device = result.scalar_one_or_none()
        return self._to_entity(project_device) if project_device else None

    async def get_by_project(self, project_id: UUID) -> list[ProjectDeviceEntity]:
        result = await self._session.execute(
            select(ProjectDevice).where(ProjectDevice.project_id == project_id)
        )

        project_devices = result.scalars().all()
        return [self._to_entity(model) for model in project_devices]

    async def get_by_device(self, device_id: UUID) -> list[ProjectDeviceEntity]:
        result = await self._session.execute(
            select(ProjectDevice).where(ProjectDevice.device_id == device_id)
        )

        project_devices = result.scalars().all()
        return [self._to_entity(model) for model in project_devices]

    async def link(self, project_device: ProjectDeviceEntity) -> None:
        self._session.add(self._to_model(project_device))

        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise

    async def update(self, project_device: ProjectDeviceEntity) -> bool:
        statement = (
            update(ProjectDevice)
            .where(ProjectDevice.id == project_device.id)
            .values(
                project_id=project_device.project_id,
                device_id=project_device.device_id,
                role=project_device.role,
            )
            .returning(ProjectDevice.id)
        )

        try:
            result = await self._session.execute(statement)
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
        return result.scalar_one_or_none() is not None

    async def delete(self, project_device_id: UUID) -> bool:
        statement = (
            delete(ProjectDevice)
            .where(ProjectDevice.id == project_device_id)
            .returning(ProjectDevice.id)
        )

        try:
            result = await self._session.execute(statement)
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()

            if getattr(error.orig, "sqlstate", None) == "23503":
                raise ProjectDeviceDeletionConflict(str(project_device_id)) from error

            raise
        return result.scalar_one_or_none() is not None

    def _to_model(self, entity: ProjectDeviceEntity) -> ProjectDevice:
        return ProjectDevice(
            id=entity.id,
            project_id=entity.project_id,
            device_id=entity.device_id,
            role=entity.role,
            created_at=entity.created_at,
        )

    def _to_entity(self, model: ProjectDevice) -> ProjectDeviceEntity:
        return ProjectDeviceEntity(
            entity_id=model.id,
            project_id=model.project_id,
            device_id=model.device_id,
            role=ProjectDeviceRole(model.role) if model.role else None,
            created_at=model.created_at,
        )
