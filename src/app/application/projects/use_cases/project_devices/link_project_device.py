from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.projects.dto import ProjectDeviceData
from app.application.projects.exceptions import DeviceNotFound
from app.application.projects.interfaces import ProjectDeviceRepository, ProjectRepository
from app.application.projects.use_cases.project_devices.project_access import ProjectAccess
from app.domain.projects import ProjectDevice, ProjectDeviceRole
from app.domain.projects.exceptions import InvalidProjectDevice


class LinkProjectDevice:
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
        project_id: UUID,
        device_id: UUID,
        role: str | None,
    ) -> ProjectDeviceData:
        await self._project_access.require_project(identity, project_id)
        try:
            now = datetime.now(UTC)
            project_device = ProjectDevice(
                entity_id=uuid4(),
                project_id=project_id,
                device_id=device_id,
                role=ProjectDeviceRole(role) if role else None,
                created_at=now,
            )
        except (InvalidProjectDevice, ValueError) as error:
            raise InvalidInput(str(error)) from error

        linked = await self._project_device_repository.link(
            identity=identity, project_device=project_device
        )
        if not linked:
            raise DeviceNotFound(str(device_id))

        return ProjectDeviceData.from_project_device(project_device)
