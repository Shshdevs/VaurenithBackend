from typing import Any
from uuid import UUID

from sqlalchemy import delete, exists, insert, literal, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Exists

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import ContainerDeletionConflict
from app.application.infrastructure.interfaces import ContainerRepository
from app.domain.infrastructure import Container as ContainerEntity
from app.domain.infrastructure import ContainerImage, ContainerName, ContainerRuntimeId
from app.infrastructure.persistence.models import Container as ContainerModel
from app.infrastructure.persistence.models import (
    Device,
    Environment,
    Project,
)
from app.infrastructure.persistence.models import (
    Service as ServiceModel,
)


class SqlAlchemyContainerRepository(ContainerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, identity: VerifiedIdentity, container_id: UUID
    ) -> ContainerEntity | None:
        result = await self._session.execute(
            select(ContainerModel)
            .join(Device, Device.id == ContainerModel.device_id)
            .where(
                ContainerModel.id == container_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )

        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_by_user(self, identity: VerifiedIdentity) -> list[ContainerEntity]:
        result = await self._session.execute(
            select(ContainerModel)
            .join(Device, Device.id == ContainerModel.device_id)
            .where(Device.user_id == identity.user_id, Device.deleted_at.is_(None))
            .order_by(ContainerModel.created_at, ContainerModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[ContainerEntity]:
        result = await self._session.execute(
            select(ContainerModel)
            .join(Device, Device.id == ContainerModel.device_id)
            .where(
                ContainerModel.device_id == device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(ContainerModel.created_at, ContainerModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[ContainerEntity]:
        result = await self._session.execute(
            select(ContainerModel)
            .join(Project, Project.id == ContainerModel.project_id)
            .join(Device, Device.id == ContainerModel.device_id)
            .where(
                ContainerModel.project_id == project_id,
                Project.user_id == identity.user_id,
                Project.deleted_at.is_(None),
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(ContainerModel.created_at, ContainerModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_environment(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[ContainerEntity]:
        result = await self._session.execute(
            select(ContainerModel)
            .join(Environment, Environment.id == ContainerModel.environment_id)
            .join(Project, Project.id == Environment.project_id)
            .join(Device, Device.id == ContainerModel.device_id)
            .where(
                ContainerModel.environment_id == environment_id,
                ContainerModel.project_id == Environment.project_id,
                Environment.deleted_at.is_(None),
                Project.user_id == identity.user_id,
                Project.deleted_at.is_(None),
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(ContainerModel.created_at, ContainerModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_service(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> list[ContainerEntity]:
        result = await self._session.execute(
            select(ContainerModel)
            .join(ServiceModel, ServiceModel.id == ContainerModel.service_id)
            .join(Device, Device.id == ContainerModel.device_id)
            .where(
                ContainerModel.service_id == service_id,
                ServiceModel.device_id == ContainerModel.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(ContainerModel.created_at, ContainerModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def create(self, identity: VerifiedIdentity, container: ContainerEntity) -> bool:
        source = (
            select(
                self._value("id", container.id),
                self._value("project_id", container.project_id),
                self._value("environment_id", container.environment_id),
                Device.id,
                self._value("service_id", container.service_id),
                self._value("container_runtime_id", container.container_runtime_id),
                self._value("name", container.name),
                self._value("slug", container.slug),
                self._value("image", container.image),
                self._value("status", container.status),
                self._value("ports", container.ports),
                self._value("volumes", container.volumes),
                self._value("networks", container.networks),
                self._value("started_at", container.started_at),
                self._value("last_seen_at", container.last_seen_at),
                self._value("metadata", container.metadata),
                self._value("version", container.version),
                self._value("created_at", container.created_at),
                self._value("updated_at", container.updated_at),
            )
            .select_from(Device)
            .where(
                Device.id == container.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
                *self._association_conditions(identity, container),
            )
        )

        statement = (
            insert(ContainerModel)
            .from_select(
                [column.name for column in ContainerModel.__table__.columns], source
            )
            .returning(ContainerModel.id)
        )

        try:
            result = await self._session.execute(statement)
        except IntegrityError:
            raise
        created_id = result.scalar_one_or_none()
        return created_id is not None

    async def update(
        self,
        identity: VerifiedIdentity,
        container: ContainerEntity,
        expected_version: int,
    ) -> bool:
        owned_device = exists(
            select(Device.id).where(
                Device.id == container.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        owned_existing_device = exists(
            select(Device.id).where(
                Device.id == ContainerModel.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        statement = (
            update(ContainerModel)
            .where(
                ContainerModel.id == container.id,
                ContainerModel.version == expected_version,
                owned_device,
                owned_existing_device,
                *self._association_conditions(identity, container),
            )
            .values(
                project_id=container.project_id,
                environment_id=container.environment_id,
                device_id=container.device_id,
                service_id=container.service_id,
                container_runtime_id=container.container_runtime_id,
                name=container.name,
                slug=container.slug,
                updated_at=container.updated_at,
                image=container.image,
                status=container.status,
                ports=container.ports,
                volumes=container.volumes,
                networks=container.networks,
                started_at=container.started_at,
                last_seen_at=container.last_seen_at,
                metadata_=container.metadata,
                version=expected_version + 1,
            )
            .returning(ContainerModel.id)
        )
        try:
            result = await self._session.execute(statement)
        except IntegrityError:
            raise
        updated_id = result.scalar_one_or_none()
        return updated_id is not None

    async def delete(self, identity: VerifiedIdentity, container_id: UUID) -> bool:
        owned_device = exists(
            select(Device.id)
            .join(ContainerModel, ContainerModel.device_id == Device.id)
            .where(
                ContainerModel.id == container_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        statement = (
            delete(ContainerModel)
            .where(ContainerModel.id == container_id, owned_device)
            .returning(ContainerModel.version)
        )
        try:
            result = await self._session.execute(statement)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) == "23503":
                raise ContainerDeletionConflict(str(container_id)) from error
            raise
        deleted_version = result.scalar_one_or_none()
        return deleted_version is not None

    @staticmethod
    def _value(column_name: str, value: Any) -> ColumnElement[Any]:
        column = ContainerModel.__table__.c[column_name]
        return literal(value, type_=column.type)

    @staticmethod
    def _association_conditions(
        identity: VerifiedIdentity, container: ContainerEntity
    ) -> list[Exists]:
        conditions = [
            exists(
                select(Device.id).where(
                    Device.id == container.device_id,
                    Device.user_id == identity.user_id,
                    Device.deleted_at.is_(None),
                )
            )
        ]

        if container.project_id is not None:
            conditions.append(
                exists(
                    select(Project.id).where(
                        Project.id == container.project_id,
                        Project.user_id == identity.user_id,
                        Project.deleted_at.is_(None),
                    )
                )
            )

        if container.environment_id is not None:
            environment_query = (
                select(Environment)
                .join(Project, Project.id == Environment.project_id)
                .where(
                    Environment.id == container.environment_id,
                    Environment.project_id == container.project_id,
                    Environment.deleted_at.is_(None),
                    Project.user_id == identity.user_id,
                    Project.deleted_at.is_(None),
                )
            )
            conditions.append(exists(environment_query))

        if container.service_id is not None:
            service_query = select(ServiceModel.id).where(
                ServiceModel.id == container.service_id,
                ServiceModel.device_id == container.device_id,
                ServiceModel.project_id == container.project_id,
                ServiceModel.environment_id == container.environment_id,
                exists(
                    select(Device.id).where(
                        Device.id == ServiceModel.device_id,
                        Device.user_id == identity.user_id,
                        Device.deleted_at.is_(None),
                    )
                ),
            )
            conditions.append(exists(service_query))

        return conditions

    @staticmethod
    def _to_entity(model: ContainerModel) -> ContainerEntity:
        return ContainerEntity(
            entity_id=model.id,
            device_id=model.device_id,
            container_runtime_id=ContainerRuntimeId(model.container_runtime_id),
            name=ContainerName(model.name),
            created_at=model.created_at,
            updated_at=model.updated_at,
            project_id=model.project_id,
            environment_id=model.environment_id,
            service_id=model.service_id,
            image=ContainerImage(model.image) if model.image is not None else None,
            status=model.status,
            ports=model.ports,
            volumes=model.volumes,
            networks=model.networks,
            started_at=model.started_at,
            last_seen_at=model.last_seen_at,
            metadata=model.metadata_,
            version=model.version,
        )
