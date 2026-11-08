from app.application.identity import VerifiedIdentity
from app.application.projects.dto import ProjectData
from app.application.projects.interfaces import ProjectRepository


class GetUserProjects:
    def __init__(self, project_repository: ProjectRepository) -> None:
        self._project_repository = project_repository

    async def execute(self, identity: VerifiedIdentity) -> list[ProjectData]:
        projects = await self._project_repository.get_user_projects(identity.user_id)
        return [ProjectData.from_project(project) for project in projects]
