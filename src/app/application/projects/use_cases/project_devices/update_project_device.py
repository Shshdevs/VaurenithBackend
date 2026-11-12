from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.projects.dto import ProjectDeviceData
from app.application.projects.exceptions import (
    DeviceNotFound,
    ProjectDeviceNotFound,
    ProjectDeviceVersionConflict,
)
from app.application.projects.interfaces import ProjectDeviceRepository, ProjectRepository
from app.application.projects.use_cases.project_devices.project_access import ProjectAccess
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.projects import (
    InvalidProjectDevice,
    ProjectDevice,
    ProjectDeviceRole,
)
from app.domain.synchronization import ChangeOperation


class UpdateProjectDevice:
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
        project_device_id: UUID,
        project_id: UUID,
        device_id: UUID,
        role: str | None,
        expected_version: int,
    ) -> ProjectDeviceData:
        try:
            existing_project_device = await self._project_device_repository.get_by_id(
                identity=identity, project_device_id=project_device_id
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
                version=existing_project_device.version + 1,
            )
        except (InvalidProjectDevice, ValueError) as error:
            raise InvalidInput(str(error)) from error

        updated_version = await self._project_device_repository.update(
            identity, project_device, expected_version
        )
        if updated_version is None:
            current = await self._project_device_repository.get_by_id(
                identity, project_device_id
            )
            if current is None:
                raise DeviceNotFound(str(device_id))
            if current.version == expected_version:
                raise DeviceNotFound(str(device_id))
            raise ProjectDeviceVersionConflict(expected_version, current.version)
        project_device = ProjectDevice(
            entity_id=project_device.id,
            project_id=project_device.project_id,
            device_id=project_device.device_id,
            role=project_device.role_value,
            created_at=project_device.created_at,
            version=updated_version,
        )
        await self._recorder.execute(
            identity,
            EntityType.PROJECT_DEVICE,
            project_device.id,
            ChangeOperation.UPDATE,
            project_device.version,
            {
                "project_id": str(project_id),
                "device_id": str(device_id),
                "role": project_device.role,
            },
        )

        return ProjectDeviceData.from_project_device(project_device)
