from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.projects.dto import ProjectDeviceData
from app.application.projects.exceptions import DeviceNotFound
from app.application.projects.interfaces import ProjectDeviceRepository, ProjectRepository
from app.application.projects.use_cases.project_devices.project_access import ProjectAccess
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.projects import ProjectDevice, ProjectDeviceRole
from app.domain.projects.exceptions import InvalidProjectDevice
from app.domain.synchronization import ChangeOperation


class LinkProjectDevice:
    def __init__(
        self,
        project_device_repository: ProjectDeviceRepository,
        project_repository: ProjectRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._project_device_repository = project_device_repository
        self._project_access = ProjectAccess(project_repository)
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
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
        await self._recorder.execute(
            identity,
            EntityType.PROJECT_DEVICE,
            project_device.id,
            ChangeOperation.INSERT,
            project_device.version,
            {
                "project_id": str(project_id),
                "device_id": str(device_id),
                "role": project_device.role,
            },
        )

        return ProjectDeviceData.from_project_device(project_device)
