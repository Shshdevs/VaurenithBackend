from uuid import UUID

from sqlalchemy import DateTime, String, delete, exists, insert, literal, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Exists

from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectDeviceDeletionConflict
from app.application.projects.interfaces import ProjectDeviceRepository
from app.domain.projects import ProjectDevice as ProjectDeviceEntity
from app.domain.projects import ProjectDeviceRole
from app.infrastructure.persistence.models import Device, Project, ProjectDevice


class SqlAlchemyProjectDeviceRepository(ProjectDeviceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, identity: VerifiedIdentity, project_device_id: UUID
    ) -> ProjectDeviceEntity | None:
        result = await self._session.execute(
            select(ProjectDevice)
            .join(Project, Project.id == ProjectDevice.project_id)
            .join(Device, Device.id == ProjectDevice.device_id)
            .where(
                ProjectDevice.id == project_device_id,
                Project.user_id == identity.user_id,
                Device.user_id == identity.user_id,
            )
        )
        project_device = result.scalar_one_or_none()
        return self._to_entity(project_device) if project_device else None

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[ProjectDeviceEntity]:
        result = await self._session.execute(
            select(ProjectDevice)
            .join(Project, Project.id == ProjectDevice.project_id)
            .join(Device, Device.id == ProjectDevice.device_id)
            .where(
                ProjectDevice.project_id == project_id,
                Project.user_id == identity.user_id,
                Device.user_id == identity.user_id,
            )
        )

        project_devices = result.scalars().all()
        return [self._to_entity(model) for model in project_devices]

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[ProjectDeviceEntity]:
        result = await self._session.execute(
            select(ProjectDevice)
            .join(Project, Project.id == ProjectDevice.project_id)
            .join(Device, Device.id == ProjectDevice.device_id)
            .where(
                ProjectDevice.device_id == device_id,
                Project.user_id == identity.user_id,
                Device.user_id == identity.user_id,
            )
        )

        project_devices = result.scalars().all()
        return [self._to_entity(model) for model in project_devices]

    async def link(
        self, identity: VerifiedIdentity, project_device: ProjectDeviceEntity
    ) -> bool:
        source = (
            select(
                literal(project_device.id),
                Project.id,
                Device.id,
                literal(project_device.role, type_=String(100)),
                literal(project_device.created_at, type_=DateTime(timezone=True)),
            )
            .select_from(Project)
            .join(Device, Device.id == project_device.device_id)
            .where(
                Project.id == project_device.project_id,
                Device.id == project_device.device_id,
                *self._association_conditions(
                    identity,
                    project_device.project_id,
                    project_device.device_id,
                    require_active_device=True,
                ),
            )
        )
        statement = (
            insert(ProjectDevice)
            .from_select(["id", "project_id", "device_id", "role", "created_at"], source)
            .returning(ProjectDevice.id)
        )

        try:
            result = await self._session.execute(statement)
        except IntegrityError:
            raise
        return result.scalar_one_or_none() is not None

    async def update(
        self, identity: VerifiedIdentity, project_device: ProjectDeviceEntity
    ) -> bool:
        statement = (
            update(ProjectDevice)
            .where(
                ProjectDevice.id == project_device.id,
                self._owned_project(identity, ProjectDevice.project_id),
                *self._association_conditions(
                    identity,
                    project_device.project_id,
                    project_device.device_id,
                    require_active_device=True,
                ),
            )
            .values(
                project_id=project_device.project_id,
                device_id=project_device.device_id,
                role=project_device.role,
            )
            .returning(ProjectDevice.id)
        )

        try:
            result = await self._session.execute(statement)
        except IntegrityError:
            raise
        return result.scalar_one_or_none() is not None

    async def delete(self, identity: VerifiedIdentity, project_device_id: UUID) -> bool:
        statement = (
            delete(ProjectDevice)
            .where(
                ProjectDevice.id == project_device_id,
                self._owned_project(identity, ProjectDevice.project_id),
                self._owned_device(identity, ProjectDevice.device_id),
            )
            .returning(ProjectDevice.id)
        )

        try:
            result = await self._session.execute(statement)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) == "23503":
                raise ProjectDeviceDeletionConflict(str(project_device_id)) from error

            raise
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _association_conditions(
        identity: VerifiedIdentity,
        project_id: UUID,
        device_id: UUID,
        require_active_device: bool = False,
    ) -> tuple[Exists, Exists]:
        return (
            SqlAlchemyProjectDeviceRepository._owned_project(identity, project_id),
            SqlAlchemyProjectDeviceRepository._owned_device(
                identity, device_id, require_active_device
            ),
        )

    @staticmethod
    def _owned_project(identity: VerifiedIdentity, project_id) -> Exists:
        return exists(
            select(Project.id).where(
                Project.id == project_id,
                Project.user_id == identity.user_id,
            )
        )

    @staticmethod
    def _owned_device(
        identity: VerifiedIdentity, device_id, require_active: bool = False
    ) -> Exists:
        conditions = [Device.id == device_id, Device.user_id == identity.user_id]
        if require_active:
            conditions.append(Device.deleted_at.is_(None))
        return exists(select(Device.id).where(*conditions))

    def _to_entity(self, model: ProjectDevice) -> ProjectDeviceEntity:
        return ProjectDeviceEntity(
            entity_id=model.id,
            project_id=model.project_id,
            device_id=model.device_id,
            role=ProjectDeviceRole(model.role) if model.role else None,
            created_at=model.created_at,
        )
