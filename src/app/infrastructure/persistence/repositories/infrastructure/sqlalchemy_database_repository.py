from typing import Any
from uuid import UUID

from sqlalchemy import delete, exists, insert, literal, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Exists

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DatabaseDeletionConflict
from app.application.infrastructure.interfaces import DatabaseRepository
from app.domain.infrastructure import (
    Database as DatabaseEntity,
)
from app.domain.infrastructure import (
    DatabaseCatalogName,
    DatabaseEndpoint,
    DatabaseResourceName,
)
from app.infrastructure.persistence.models import (
    Container,
    Device,
    Environment,
    Project,
    Service,
)
from app.infrastructure.persistence.models import (
    Database as DatabaseModel,
)


class SqlAlchemyDatabaseRepository(DatabaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, identity: VerifiedIdentity, database_id: UUID
    ) -> DatabaseEntity | None:
        result = await self._session.execute(
            select(DatabaseModel)
            .join(Device, Device.id == DatabaseModel.device_id)
            .where(
                DatabaseModel.id == database_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_by_user(self, identity: VerifiedIdentity) -> list[DatabaseEntity]:
        result = await self._session.execute(
            select(DatabaseModel)
            .join(Device, Device.id == DatabaseModel.device_id)
            .where(
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(DatabaseModel.created_at, DatabaseModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[DatabaseEntity]:
        result = await self._session.execute(
            select(DatabaseModel)
            .join(Device, Device.id == DatabaseModel.device_id)
            .where(
                DatabaseModel.device_id == device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(DatabaseModel.created_at, DatabaseModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[DatabaseEntity]:
        result = await self._session.execute(
            select(DatabaseModel)
            .join(Project, Project.id == DatabaseModel.project_id)
            .join(Device, Device.id == DatabaseModel.device_id)
            .where(
                DatabaseModel.project_id == project_id,
                Project.user_id == identity.user_id,
                Project.deleted_at.is_(None),
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(DatabaseModel.created_at, DatabaseModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_environment(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[DatabaseEntity]:
        result = await self._session.execute(
            select(DatabaseModel)
            .join(Environment, Environment.id == DatabaseModel.environment_id)
            .join(Project, Project.id == Environment.project_id)
            .join(Device, Device.id == DatabaseModel.device_id)
            .where(
                DatabaseModel.environment_id == environment_id,
                DatabaseModel.project_id == Environment.project_id,
                Environment.deleted_at.is_(None),
                Project.user_id == identity.user_id,
                Project.deleted_at.is_(None),
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(DatabaseModel.created_at, DatabaseModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_container(
        self, identity: VerifiedIdentity, container_id: UUID
    ) -> list[DatabaseEntity]:
        result = await self._session.execute(
            select(DatabaseModel)
            .join(Container, Container.id == DatabaseModel.container_id)
            .join(Device, Device.id == DatabaseModel.device_id)
            .where(
                DatabaseModel.container_id == container_id,
                Container.device_id == DatabaseModel.device_id,
                Container.project_id == DatabaseModel.project_id,
                Container.environment_id == DatabaseModel.environment_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(DatabaseModel.created_at, DatabaseModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_service(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> list[DatabaseEntity]:
        result = await self._session.execute(
            select(DatabaseModel)
            .join(Service, Service.id == DatabaseModel.service_id)
            .join(Device, Device.id == DatabaseModel.device_id)
            .where(
                DatabaseModel.service_id == service_id,
                Service.device_id == DatabaseModel.device_id,
                Service.project_id == DatabaseModel.project_id,
                Service.environment_id == DatabaseModel.environment_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(DatabaseModel.created_at, DatabaseModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def create(self, identity: VerifiedIdentity, database: DatabaseEntity) -> bool:
        source = (
            select(
                self._value("id", database.id),
                self._value("project_id", database.project_id),
                self._value("environment_id", database.environment_id),
                Device.id,
                self._value("container_id", database.container_id),
                self._value("service_id", database.service_id),
                self._value("name", database.name),
                self._value("slug", database.slug),
                self._value("dbms_type", database.dbms_type),
                self._value("host", database.host),
                self._value("port", database.port),
                self._value("database_name", database.database_name),
                self._value("status", database.status),
                self._value("last_checked_at", database.last_checked_at),
                self._value("metadata", database.metadata),
                self._value("version", database.version),
                self._value("created_at", database.created_at),
                self._value("updated_at", database.updated_at),
            )
            .select_from(Device)
            .where(
                Device.id == database.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
                *self._association_conditions(identity, database),
            )
        )
        statement = (
            insert(DatabaseModel)
            .from_select(
                [column.name for column in DatabaseModel.__table__.columns], source
            )
            .returning(DatabaseModel.id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def update(
        self,
        identity: VerifiedIdentity,
        database: DatabaseEntity,
        expected_version: int,
    ) -> bool:
        owned_device = exists(
            select(Device.id).where(
                Device.id == database.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        owned_existing_device = exists(
            select(Device.id).where(
                Device.id == DatabaseModel.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        statement = (
            update(DatabaseModel)
            .where(
                DatabaseModel.id == database.id,
                DatabaseModel.version == expected_version,
                owned_device,
                owned_existing_device,
                *self._association_conditions(identity, database),
            )
            .values(
                project_id=database.project_id,
                environment_id=database.environment_id,
                device_id=database.device_id,
                container_id=database.container_id,
                service_id=database.service_id,
                name=database.name,
                slug=database.slug,
                dbms_type=database.dbms_type,
                host=database.host,
                port=database.port,
                database_name=database.database_name,
                status=database.status,
                last_checked_at=database.last_checked_at,
                metadata_=database.metadata,
                updated_at=database.updated_at,
                version=expected_version + 1,
            )
            .returning(DatabaseModel.id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def delete(self, identity: VerifiedIdentity, database_id: UUID) -> bool:
        owned_device = exists(
            select(Device.id).where(
                Device.id == DatabaseModel.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        statement = (
            delete(DatabaseModel)
            .where(DatabaseModel.id == database_id, owned_device)
            .returning(DatabaseModel.id)
        )
        try:
            result = await self._session.execute(statement)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) == "23503":
                raise DatabaseDeletionConflict(str(database_id)) from error
            raise
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _value(column_name: str, value: Any) -> ColumnElement[Any]:
        column = DatabaseModel.__table__.c[column_name]
        return literal(value, type_=column.type)

    @staticmethod
    def _association_conditions(
        identity: VerifiedIdentity, database: DatabaseEntity
    ) -> list[Exists]:
        conditions = [
            exists(
                select(Device.id).where(
                    Device.id == database.device_id,
                    Device.user_id == identity.user_id,
                    Device.deleted_at.is_(None),
                )
            )
        ]
        if database.project_id is not None:
            conditions.append(
                exists(
                    select(Project.id).where(
                        Project.id == database.project_id,
                        Project.user_id == identity.user_id,
                        Project.deleted_at.is_(None),
                    )
                )
            )
        if database.environment_id is not None:
            conditions.append(
                exists(
                    select(Environment.id)
                    .join(Project, Project.id == Environment.project_id)
                    .where(
                        Environment.id == database.environment_id,
                        Environment.project_id == database.project_id,
                        Environment.deleted_at.is_(None),
                        Project.user_id == identity.user_id,
                        Project.deleted_at.is_(None),
                    )
                )
            )
        if database.container_id is not None:
            container_conditions = [
                Container.id == database.container_id,
                Container.device_id == database.device_id,
                Container.project_id == database.project_id,
                Container.environment_id == database.environment_id,
                exists(
                    select(Device.id).where(
                        Device.id == Container.device_id,
                        Device.user_id == identity.user_id,
                        Device.deleted_at.is_(None),
                    )
                ),
            ]
            if database.service_id is not None:
                container_conditions.append(Container.service_id == database.service_id)
            conditions.append(exists(select(Container.id).where(*container_conditions)))
        if database.service_id is not None:
            conditions.append(
                exists(
                    select(Service.id).where(
                        Service.id == database.service_id,
                        Service.device_id == database.device_id,
                        Service.project_id == database.project_id,
                        Service.environment_id == database.environment_id,
                        exists(
                            select(Device.id).where(
                                Device.id == Service.device_id,
                                Device.user_id == identity.user_id,
                                Device.deleted_at.is_(None),
                            )
                        ),
                    )
                )
            )
        return conditions

    @staticmethod
    def _to_entity(model: DatabaseModel) -> DatabaseEntity:
        endpoint = (
            DatabaseEndpoint(host=model.host, port=model.port)
            if model.host is not None or model.port is not None
            else None
        )
        return DatabaseEntity(
            entity_id=model.id,
            device_id=model.device_id,
            name=DatabaseResourceName(model.name),
            dbms_type=model.dbms_type,
            created_at=model.created_at,
            updated_at=model.updated_at,
            project_id=model.project_id,
            environment_id=model.environment_id,
            container_id=model.container_id,
            service_id=model.service_id,
            endpoint=endpoint,
            database_name=(
                DatabaseCatalogName(model.database_name)
                if model.database_name is not None
                else None
            ),
            status=model.status,
            last_checked_at=model.last_checked_at,
            metadata=model.metadata_,
            version=model.version,
        )
