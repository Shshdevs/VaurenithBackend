from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.projects.dto import ProjectDeviceData
from app.application.projects.exceptions import ProjectDeviceNotFound
from app.application.projects.interfaces import ProjectDeviceRepository, ProjectRepository
from app.application.projects.use_cases.project_devices.project_access import ProjectAccess
from app.domain.projects import (
    InvalidProjectDevice,
    ProjectDevice,
    ProjectDeviceRole,
)


class UpdateProjectDevice:
    def __init__(
        self,
        project_device_repository: ProjectDeviceRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self._project_device_repository = project_device_repository
        self._project_access = ProjectAccess(project_repository)

    async def execute(
        self,
        identity: VerifiedIdentity,
        project_device_id: UUID,
        project_id: UUID,
        device_id: UUID,
        role: str | None,
    ) -> ProjectDeviceData:
        try:
            existing_project_device = await self._project_device_repository.get_by_id(
                project_device_id=project_device_id
            )
            if not existing_project_device:
                raise ProjectDeviceNotFound(str(project_device_id))
            await self._project_access.require_project(
                identity, existing_project_device.project_id
            )
            await self._project_access.require_project(identity, project_id)
            project_device_role = ProjectDeviceRole(role) if role else None
            project_device = ProjectDevice(
                entity_id=project_device_id,
                project_id=project_id,
                device_id=device_id,
                role=project_device_role,
                created_at=existing_project_device.created_at,
            )
        except (InvalidProjectDevice, ValueError) as error:
            raise InvalidInput(str(error)) from error

        result = await self._project_device_repository.update(project_device)
        if not result:
            raise ProjectDeviceNotFound(str(project_device_id))

        return ProjectDeviceData.from_project_device(project_device)
