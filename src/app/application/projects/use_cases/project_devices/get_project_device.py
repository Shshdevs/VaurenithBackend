from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.projects.dto import ProjectDeviceData
from app.application.projects.exceptions import ProjectDeviceNotFound
from app.application.projects.interfaces import ProjectDeviceRepository, ProjectRepository
from app.application.projects.use_cases.project_devices.project_access import ProjectAccess


class GetProjectDevice:
    def __init__(
        self,
        project_device_repository: ProjectDeviceRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self._project_device_repository = project_device_repository
        self._project_access = ProjectAccess(project_repository)

    async def execute(
        self, identity: VerifiedIdentity, project_device_id: UUID
    ) -> ProjectDeviceData:
        project_device = await self._project_device_repository.get_by_id(
            identity=identity, project_device_id=project_device_id
        )

        if not project_device:
            raise ProjectDeviceNotFound(str(project_device_id))
        await self._project_access.require_project(identity, project_device.project_id)
        return ProjectDeviceData.from_project_device(project_device)
