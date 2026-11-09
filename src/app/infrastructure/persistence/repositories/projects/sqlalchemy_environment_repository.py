from typing import Any
from uuid import UUID

from sqlalchemy import delete, exists, insert, literal, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Exists

from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import EnvironmentDeletionConflict
from app.application.projects.interfaces import EnvironmentRepository
from app.domain.projects import Environment as EnvironmentEntity
from app.domain.projects import EnvironmentName, EnvironmentType
from app.infrastructure.persistence.models.projects import Environment, Project


class SqlAlchemyEnvironmentRepository(EnvironmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> EnvironmentEntity | None:
        result = await self._session.execute(
            select(Environment)
            .join(Project, Project.id == Environment.project_id)
            .where(
                Environment.id == environment_id,
                Environment.deleted_at.is_(None),
                Project.user_id == identity.user_id,
                Project.deleted_at.is_(None),
            )
        )

        environment = result.scalar_one_or_none()
        return self._to_entity(environment) if environment else None

    async def get_active_by_project_id(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[EnvironmentEntity]:
        result = await self._session.execute(
            select(Environment)
            .join(Project, Project.id == Environment.project_id)
            .where(
                Environment.project_id == project_id,
                Environment.deleted_at.is_(None),
                Project.user_id == identity.user_id,
                Project.deleted_at.is_(None),
            )
        )
        environments = result.scalars().all()
        return [self._to_entity(model) for model in environments]

    async def create(
        self, identity: VerifiedIdentity, environment: EnvironmentEntity
    ) -> bool:
        source = (
            select(
                self._value("id", environment.id),
                Project.id,
                self._value("name", environment.name),
                self._value("slug", environment.slug),
                self._value("environment_type", environment.environment_type),
                self._value("description", environment.description),
                self._value("configuration", environment.configuration),
                self._value("version", environment.version),
                self._value("created_at", environment.created_at),
                self._value("updated_at", environment.updated_at),
                self._value("deleted_at", environment.deleted_at),
            )
            .select_from(Project)
            .where(
                Project.id == environment.project_id,
                Project.user_id == identity.user_id,
                Project.deleted_at.is_(None),
            )
        )
        statement = (
            insert(Environment)
            .from_select([column.name for column in Environment.__table__.columns], source)
            .returning(Environment.id)
        )
        try:
            result = await self._session.execute(statement)
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
        return result.scalar_one_or_none() is not None

    async def update(
        self,
        identity: VerifiedIdentity,
        environment: EnvironmentEntity,
        expected_version: int,
    ) -> bool:
        statement = (
            update(Environment)
            .where(
                self._owned_environment(
                    identity,
                    environment.id,
                    environment.project_id,
                    expected_version,
                )
            )
            .values(
                name=environment.name,
                slug=environment.slug,
                environment_type=environment.environment_type,
                description=environment.description,
                configuration=environment.configuration,
                updated_at=environment.updated_at,
                version=expected_version + 1,
            )
            .returning(Environment.id)
        )

        try:
            result = await self._session.execute(statement)
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
        return result.scalar_one_or_none() is not None

    async def delete(self, identity: VerifiedIdentity, environment_id: UUID) -> bool:
        statement = (
            delete(Environment)
            .where(self._owned_environment(identity, environment_id))
            .returning(Environment.id)
        )
        try:
            result = await self._session.execute(statement)
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            if getattr(error.orig, "sqlstate", None) == "23503":
                raise EnvironmentDeletionConflict(str(environment_id)) from error
            raise
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _owned_environment(
        identity: VerifiedIdentity,
        environment_id: UUID,
        project_id: UUID | None = None,
        expected_version: int | None = None,
    ) -> Exists:
        conditions = [
            Environment.id == environment_id,
            Environment.deleted_at.is_(None),
            Project.user_id == identity.user_id,
            Project.deleted_at.is_(None),
        ]
        if project_id is not None:
            conditions.append(Environment.project_id == project_id)
        if expected_version is not None:
            conditions.append(Environment.version == expected_version)
        return exists(
            select(Environment.id)
            .join(Project, Project.id == Environment.project_id)
            .where(*conditions)
        )

    @staticmethod
    def _value(column_name: str, value: Any) -> ColumnElement[Any]:
        column = Environment.__table__.c[column_name]
        return literal(value, type_=column.type)

    @staticmethod
    def _to_entity(model: Environment) -> EnvironmentEntity:
        return EnvironmentEntity(
            entity_id=model.id,
            project_id=model.project_id,
            name=EnvironmentName(model.name),
            environment_type=EnvironmentType(model.environment_type),
            description=model.description,
            configuration=model.configuration,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
            deleted_at=model.deleted_at,
        )
