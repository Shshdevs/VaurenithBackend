from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity.dto import VerifiedIdentity
from app.application.projects.dto import ProjectData
from app.application.projects.exceptions import ProjectNotFound, ProjectVersionConflict
from app.application.projects.interfaces import ProjectRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.projects import (
    InvalidProject,
    Project,
    ProjectName,
    ProjectStatus,
    ProjectType,
)
from app.domain.synchronization import ChangeOperation


class UpdateProject:
    def __init__(
        self, project_repository: ProjectRepository, recorder: ChangeRecorder
    ) -> None:
        self._project_repository = project_repository
        self._recorder = recorder

    async def execute(
        self,
        identity: VerifiedIdentity,
        project_id: UUID,
        name: str,
        project_type: ProjectType,
        status: ProjectStatus,
        expected_version: int,
        description: str | None,
        metadata: dict[str, Any] | None,
    ) -> ProjectData:
        existing_project = await self._project_repository.get_by_id(
            user_id=identity.user_id,
            project_id=project_id,
        )
        if existing_project is None:
            raise ProjectNotFound(str(project_id))
        if existing_project.version != expected_version:
            raise ProjectVersionConflict(expected_version, existing_project.version)

        try:
            project_name = ProjectName(name)
            now = datetime.now(UTC)
            project = Project(
                entity_id=project_id,
                user_id=identity.user_id,
                name=project_name,
                description=description,
                project_type=ProjectType(project_type),
                status=ProjectStatus(status),
                metadata=metadata,
                version=expected_version + 1,
                created_at=existing_project.created_at,
                updated_at=now,
                deleted_at=existing_project.deleted_at,
            )
        except (InvalidProject, ValueError) as error:
            raise InvalidInput(str(error)) from error

        result = await self._project_repository.update(
            identity.user_id, project=project, expected_version=expected_version
        )
        if not result:
            raise ProjectVersionConflict(expected_version)
        await self._recorder.execute(
            identity,
            EntityType.PROJECT,
            project.id,
            ChangeOperation.UPDATE,
            project.version,
            {
                "name": project.name,
                "description": project.description,
                "project_type": project.project_type.value,
                "status": project.status.value,
            },
        )

        return ProjectData.from_project(project)
