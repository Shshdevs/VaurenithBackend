from app.application.identity import VerifiedIdentity
from app.application.projects.dto.project_data import ProjectData
from app.application.projects.interfaces.project_repository import ProjectRepository


class GetUserProjects:
    def __init__(self, project_repository: ProjectRepository) -> None:
        self._project_repository = project_repository

    async def execute(self, identity: VerifiedIdentity) -> list[ProjectData]:
        projects = await self._project_repository.get_user_projects(identity.user_id)
        return [
            ProjectData(
                id=project.id,
                user_id=project.user_id,
                name=project.name,
                description=project.description,
                project_type=project.project_type.value,
                status=project.status.value,
                metadata=project.metadata,
                version=project.version,
                created_at=project.created_at,
                updated_at=project.updated_at,
                deleted_at=project.deleted_at,
            )
            for project in projects
        ]
