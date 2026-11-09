from uuid import UUID

from sqlalchemy import delete, exists, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Exists

from app.application.projects.exceptions import EnvironmentDeletionConflict
from app.application.projects.interfaces import EnvironmentRepository
from app.domain.projects import Environment as EnvironmentEntity
from app.domain.projects import EnvironmentName, EnvironmentType
from app.infrastructure.persistence.models.projects import Environment


class SqlAlchemyEnvironmentRepository(EnvironmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, environment_id: UUID) -> EnvironmentEntity | None:
        result = await self._session.execute(
            select(Environment).where(self._active_environment(environment_id))
        )

        environment = result.scalar_one_or_none()
        return self._to_entity(environment) if environment else None

    async def get_active_by_project_id(self, project_id: UUID) -> list[EnvironmentEntity]:
        result = await self._session.execute(
            select(Environment).where(
                Environment.project_id == project_id, Environment.deleted_at.is_(None)
            )
        )
        environments = result.scalars().all()
        return [self._to_entity(model) for model in environments]

    async def create(self, environment: EnvironmentEntity) -> None:
        self._session.add(self._to_model(environment))

        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise

    async def update(self, environment: EnvironmentEntity) -> bool:
        statement = (
            update(Environment)
            .where(self._active_environment(environment.id))
            .values(
                project_id=environment.project_id,
                name=environment.name,
                slug=environment.slug,
                environment_type=environment.environment_type,
                description=environment.description,
                configuration=environment.configuration,
                created_at=environment.created_at,
                updated_at=environment.updated_at,
                deleted_at=environment.deleted_at,
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

    async def delete(self, environment_id: UUID) -> bool:
        statement = (
            delete(Environment)
            .where(self._active_environment(environment_id))
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
    def _active_environment(environment_id) -> Exists:
        return exists(
            select(Environment.id).where(
                Environment.id == environment_id,
                Environment.deleted_at.is_(None),
            )
        )

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
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _to_model(entity: EnvironmentEntity) -> Environment:
        return Environment(
            id=entity.id,
            project_id=entity.project_id,
            name=entity.name,
            slug=entity.slug,
            environment_type=entity.environment_type,
            description=entity.description,
            configuration=entity.configuration,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )
