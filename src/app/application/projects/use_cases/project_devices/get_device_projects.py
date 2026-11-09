from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.projects.dto import ProjectDeviceData
from app.application.projects.interfaces import ProjectDeviceRepository, ProjectRepository
from app.application.projects.use_cases.project_devices.project_access import ProjectAccess


class GetDeviceProjects:
    def __init__(
        self,
        project_device_repository: ProjectDeviceRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self._project_device_repository = project_device_repository
        self._project_access = ProjectAccess(project_repository)

    async def execute(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[ProjectDeviceData]:
        project_devices = await self._project_device_repository.get_by_device(
            device_id=device_id
        )
        project_ids = await self._project_access.get_user_project_ids(identity)
        return [
            ProjectDeviceData.from_project_device(project_device)
            for project_device in project_devices
            if project_device.project_id in project_ids
        ]
