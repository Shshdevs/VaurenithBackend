from typing import Any
from uuid import UUID

from sqlalchemy import delete, exists, insert, literal, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Exists

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import ServiceDeletionConflict
from app.application.infrastructure.interfaces import ServiceRepository
from app.domain.infrastructure import Service as ServiceEntity
from app.domain.infrastructure import ServiceName, SystemIdentifier
from app.infrastructure.persistence.models import Device, Environment, Project
from app.infrastructure.persistence.models import Service as ServiceModel


class SqlAlchemyServiceRepository(ServiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user(self, identity: VerifiedIdentity) -> list[ServiceEntity]:
        result = await self._session.execute(
            select(ServiceModel)
            .join(Device, Device.id == ServiceModel.device_id)
            .where(Device.user_id == identity.user_id)
            .order_by(ServiceModel.created_at, ServiceModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_id(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> ServiceEntity | None:
        result = await self._session.execute(
            select(ServiceModel)
            .join(Device, Device.id == ServiceModel.device_id)
            .where(
                ServiceModel.id == service_id,
                Device.user_id == identity.user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[ServiceEntity]:
        result = await self._session.execute(
            select(ServiceModel)
            .join(Device, Device.id == ServiceModel.device_id)
            .where(
                ServiceModel.device_id == device_id,
                Device.user_id == identity.user_id,
            )
            .order_by(ServiceModel.created_at, ServiceModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[ServiceEntity]:
        result = await self._session.execute(
            select(ServiceModel)
            .join(Project, Project.id == ServiceModel.project_id)
            .join(Device, Device.id == ServiceModel.device_id)
            .where(
                ServiceModel.project_id == project_id,
                Project.user_id == identity.user_id,
                Project.deleted_at.is_(None),
                Device.user_id == identity.user_id,
            )
            .order_by(ServiceModel.created_at, ServiceModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_environment(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[ServiceEntity]:
        result = await self._session.execute(
            select(ServiceModel)
            .join(Environment, Environment.id == ServiceModel.environment_id)
            .join(Project, Project.id == Environment.project_id)
            .join(Device, Device.id == ServiceModel.device_id)
            .where(
                ServiceModel.environment_id == environment_id,
                Environment.deleted_at.is_(None),
                Project.user_id == identity.user_id,
                Project.deleted_at.is_(None),
                Device.user_id == identity.user_id,
            )
            .order_by(ServiceModel.created_at, ServiceModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def create(self, identity: VerifiedIdentity, service: ServiceEntity) -> bool:
        source = (
            select(
                self._value("id", service.id),
                self._value("project_id", service.project_id),
                self._value("environment_id", service.environment_id),
                Device.id,
                self._value("name", service.name),
                self._value("slug", service.slug),
                self._value("service_type", service.service_type),
                self._value("description", service.description),
                self._value("system_identifier", service.system_identifier),
                self._value("status", service.status),
                self._value("last_status_at", service.last_status_at),
                self._value("metadata", service.metadata),
                self._value("version", service.version),
                self._value("created_at", service.created_at),
                self._value("updated_at", service.updated_at),
            )
            .select_from(Device)
            .where(
                Device.id == service.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
                *self._association_conditions(identity, service),
            )
        )
        statement = (
            insert(ServiceModel)
            .from_select([column.name for column in ServiceModel.__table__.columns], source)
            .returning(ServiceModel.id)
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
        service: ServiceEntity,
        expected_version: int,
    ) -> bool:
        owned_device = exists(
            select(Device.id).where(
                Device.id == ServiceModel.device_id,
                Device.user_id == identity.user_id,
            )
        )
        statement = (
            update(ServiceModel)
            .where(
                ServiceModel.id == service.id,
                ServiceModel.version == expected_version,
                owned_device,
                *self._association_conditions(identity, service),
            )
            .values(
                project_id=service.project_id,
                environment_id=service.environment_id,
                device_id=service.device_id,
                name=service.name,
                slug=service.slug,
                service_type=service.service_type,
                description=service.description,
                system_identifier=service.system_identifier,
                status=service.status,
                last_status_at=service.last_status_at,
                metadata_=service.metadata,
                version=expected_version + 1,
                updated_at=service.updated_at,
            )
            .returning(ServiceModel.id)
        )
        try:
            result = await self._session.execute(statement)
        except IntegrityError:
            raise
        updated_id = result.scalar_one_or_none()
        return updated_id is not None

    async def delete(self, identity: VerifiedIdentity, service_id: UUID) -> bool:
        owned_device = exists(
            select(Device.id)
            .join(ServiceModel, ServiceModel.device_id == Device.id)
            .where(
                ServiceModel.id == service_id,
                Device.user_id == identity.user_id,
            )
        )
        statement = (
            delete(ServiceModel)
            .where(ServiceModel.id == service_id, owned_device)
            .returning(ServiceModel.version)
        )
        try:
            result = await self._session.execute(statement)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) == "23503":
                raise ServiceDeletionConflict(str(service_id)) from error
            raise
        deleted_version = result.scalar_one_or_none()
        return deleted_version is not None

    @staticmethod
    def _value(column_name: str, value: Any) -> ColumnElement[Any]:
        column = ServiceModel.__table__.c[column_name]
        return literal(value, type_=column.type)

    @staticmethod
    def _association_conditions(
        identity: VerifiedIdentity, service: ServiceEntity
    ) -> list[Exists]:
        conditions = [
            exists(
                select(Device.id).where(
                    Device.id == service.device_id,
                    Device.user_id == identity.user_id,
                    Device.deleted_at.is_(None),
                )
            )
        ]
        if service.project_id is not None:
            conditions.append(
                exists(
                    select(Project.id).where(
                        Project.id == service.project_id,
                        Project.user_id == identity.user_id,
                        Project.deleted_at.is_(None),
                    )
                )
            )
        if service.environment_id is not None:
            environment_query = (
                select(Environment.id)
                .join(Project, Project.id == Environment.project_id)
                .where(
                    Environment.id == service.environment_id,
                    Environment.deleted_at.is_(None),
                    Project.user_id == identity.user_id,
                    Project.deleted_at.is_(None),
                )
            )
            if service.project_id is not None:
                environment_query = environment_query.where(
                    Environment.project_id == service.project_id
                )
            conditions.append(exists(environment_query))
        return conditions

    @staticmethod
    def _to_entity(model: ServiceModel) -> ServiceEntity:
        return ServiceEntity(
            entity_id=model.id,
            project_id=model.project_id,
            environment_id=model.environment_id,
            device_id=model.device_id,
            name=ServiceName(model.name),
            service_type=model.service_type,
            description=model.description,
            system_identifier=(
                SystemIdentifier(model.system_identifier)
                if model.system_identifier is not None
                else None
            ),
            status=model.status,
            last_status_at=model.last_status_at,
            metadata=model.metadata_,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
