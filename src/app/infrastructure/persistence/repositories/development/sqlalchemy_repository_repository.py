from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Exists

from app.application.development.interfaces import RepositoryRepository
from app.domain.development.entities.repository import Repository as RepositoryEntity
from app.infrastructure.persistence.models.development.repository import Repository
from app.infrastructure.persistence.models.projects.project import Project


class SqlAlchemyRepositoryRepository(RepositoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, user_id: UUID, repository_id: UUID
    ) -> RepositoryEntity | None:
        result = await self._session.execute(
            select(Repository).where(
                Repository.id == repository_id,
                self._owned_project(user_id, Repository.project_id),
                Repository.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_by_user(self, user_id: UUID) -> list[RepositoryEntity]:
        result = await self._session.execute(
            select(Repository)
            .join(Project, Project.id == Repository.project_id)
            .where(
                Project.user_id == user_id,
                Project.deleted_at.is_(None),
                Repository.deleted_at.is_(None),
            )
            .order_by(Repository.created_at, Repository.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_project(
        self, user_id: UUID, project_id: UUID
    ) -> list[RepositoryEntity]:
        result = await self._session.execute(
            select(Repository)
            .join(Project, Project.id == Repository.project_id)
            .where(
                Project.id == project_id,
                Project.user_id == user_id,
                Project.deleted_at.is_(None),
                Repository.deleted_at.is_(None),
            )
            .order_by(Repository.created_at, Repository.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def create(self, repository: RepositoryEntity) -> None:
        self._session.add(self._to_model(repository))

    async def update(
        self, user_id: UUID, repository: RepositoryEntity, expected_version: int
    ) -> bool:
        result = await self._session.execute(
            update(Repository)
            .where(
                Repository.id == repository.id,
                self._owned_project(user_id, Repository.project_id),
                Repository.deleted_at.is_(None),
                Repository.version == expected_version,
            )
            .values(
                name=repository.name,
                slug=repository.slug,
                description=repository.description,
                remote_url=repository.remote_url,
                default_branch=repository.default_branch,
                repository_type=repository.repository_type,
                version=repository.version,
                updated_at=repository.updated_at,
                deleted_at=repository.deleted_at,
            )
            .returning(Repository.id)
        )
        return result.scalar_one_or_none() is not None

    async def delete(
        self, user_id: UUID, repository_id: UUID, expected_version: int
    ) -> bool:
        deleted_at = datetime.now(UTC)
        result = await self._session.execute(
            update(Repository)
            .where(
                Repository.id == repository_id,
                self._owned_project(user_id, Repository.project_id),
                Repository.deleted_at.is_(None),
                Repository.version == expected_version,
            )
            .values(
                deleted_at=deleted_at,
                updated_at=deleted_at,
                version=expected_version + 1,
            )
            .returning(Repository.id)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _owned_project(user_id: UUID, project_id) -> Exists:
        return exists(
            select(Project.id).where(
                Project.id == project_id,
                Project.user_id == user_id,
                Project.deleted_at.is_(None),
            )
        )

    @staticmethod
    def _to_entity(model: Repository) -> RepositoryEntity:
        return RepositoryEntity(
            entity_id=model.id,
            project_id=model.project_id,
            name=model.name,
            created_at=model.created_at,
            updated_at=model.updated_at,
            description=model.description,
            remote_url=model.remote_url,
            default_branch=model.default_branch,
            repository_type=model.repository_type,
            version=model.version,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _to_model(entity: RepositoryEntity) -> Repository:
        return Repository(
            id=entity.id,
            project_id=entity.project_id,
            name=entity.name,
            slug=entity.slug,
            description=entity.description,
            remote_url=entity.remote_url,
            default_branch=entity.default_branch,
            repository_type=entity.repository_type,
            version=entity.version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )
