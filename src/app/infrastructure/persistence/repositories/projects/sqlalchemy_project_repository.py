from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects import ProjectRepository
from app.domain.projects import Project as ProjectEntity
from app.domain.projects import ProjectName
from app.infrastructure.persistence.models.projects import Project


class SqlAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: UUID) -> ProjectEntity | None:
        pass

    async def create(self, project: ProjectEntity) -> None:
        project_model = Project(
            id=project.id,
            user_id=project.user_id,
            name=project.name,
            description=project.description,
            project_type=project.project_type,
            status=project.status,
            metadata_=project.metadata,
            version=project.version,
            created_at=project.created_at,
            updated_at=project.updated_at,
            deleted_at=project.deleted_at,
        )

        self._session.add(project_model)

        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise

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

    async def get_user_projects(self, user_id: UUID) -> list[ProjectEntity]:
        raise NotImplementedError

    async def update(self, project: ProjectEntity) -> None:
        raise NotImplementedError

    async def delete(self, user_id: UUID, project_id: UUID) -> None:
        raise NotImplementedError
