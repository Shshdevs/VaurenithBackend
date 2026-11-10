from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectDeviceNotFound
from app.application.projects.interfaces import ProjectDeviceRepository, ProjectRepository
from app.application.projects.use_cases.project_devices.project_access import ProjectAccess
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteProjectDevice:
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
    async def execute(self, identity: VerifiedIdentity, project_device_id: UUID) -> None:
        project_device = await self._project_device_repository.get_by_id(
            identity=identity, project_device_id=project_device_id
        )
        if project_device is None:
            raise ProjectDeviceNotFound(str(project_device_id))
        await self._project_access.require_project(identity, project_device.project_id)
        result = await self._project_device_repository.delete(
            identity=identity, project_device_id=project_device_id
        )

        if not result:
            raise ProjectDeviceNotFound(str(project_device_id))
        await self._recorder.execute(
            identity,
            EntityType.PROJECT_DEVICE,
            project_device_id,
            ChangeOperation.DELETE,
            project_device.version + 1,
        )
