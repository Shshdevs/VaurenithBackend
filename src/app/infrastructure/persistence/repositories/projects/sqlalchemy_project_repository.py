from uuid import UUID

from sqlalchemy import delete, exists, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Exists

from app.application.projects.exceptions import ProjectDeletionConflict
from app.application.projects.interfaces import ProjectRepository
from app.domain.projects import Project as ProjectEntity
from app.domain.projects import ProjectName, ProjectStatus
from app.infrastructure.persistence.models.projects import Project


class SqlAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID, project_id: UUID) -> ProjectEntity | None:
        result = await self._session.execute(
            select(Project).where(
                self._owned_project(user_id, project_id), Project.deleted_at.is_(None)
            )
        )
        project = result.scalar_one_or_none()
        return self._to_entity(project) if project is not None else None

    async def create(self, project: ProjectEntity) -> None:
        self._session.add(self._to_model(project))

        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise

    async def get_user_projects(self, user_id: UUID) -> list[ProjectEntity]:
        result = await self._session.execute(
            select(Project).where(
                Project.user_id == user_id,
                Project.status != ProjectStatus.ARCHIVED,
                Project.deleted_at.is_(None),
            )
        )
        projects = result.scalars().all()
        return [self._to_entity(model) for model in projects]

    async def update(
        self, user_id: UUID, project: ProjectEntity, expected_version: int
    ) -> bool:
        statement = (
            update(Project)
            .where(
                self._owned_project(user_id, project.id),
                Project.deleted_at.is_(None),
                Project.version == expected_version,
            )
            .values(
                name=project.name,
                slug=project.slug,
                description=project.description,
                project_type=project.project_type,
                status=project.status,
                metadata_=project.metadata,
                version=expected_version + 1,
                updated_at=project.updated_at,
                deleted_at=project.deleted_at,
            )
            .returning(Project.id)
        )

        try:
            result = await self._session.execute(statement)
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
        return result.scalar_one_or_none() is not None

    async def delete(self, user_id: UUID, project_id: UUID) -> bool:
        statement = (
            delete(Project)
            .where(self._owned_project(user_id, project_id))
            .returning(Project.id)
        )

        try:
            result = await self._session.execute(statement)
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            if getattr(error.orig, "sqlstate", None) == "23503":
                raise ProjectDeletionConflict(str(project_id)) from error
            raise
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _owned_project(user_id: UUID, project_id) -> Exists:
        return exists(
            select(Project.id).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
        )

    @staticmethod
    def _to_entity(model: Project) -> ProjectEntity:
        return ProjectEntity(
            entity_id=model.id,
            user_id=model.user_id,
            name=ProjectName(model.name),
            description=model.description,
            project_type=model.project_type,
            status=model.status,
            metadata=model.metadata_,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _to_model(entity: ProjectEntity) -> Project:
        return Project(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            slug=entity.slug,
            description=entity.description,
            project_type=entity.project_type,
            status=entity.status,
            metadata_=entity.metadata,
            version=entity.version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )
