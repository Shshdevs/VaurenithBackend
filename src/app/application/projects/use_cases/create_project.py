from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.projects import ProjectData, ProjectRepository
from app.domain.projects import (
    InvalidProject,
    Project,
    ProjectName,
    ProjectStatus,
    ProjectType,
)


class CreateProject:
    def __init__(self, project_repository: ProjectRepository) -> None:
        self._project_repository = project_repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        name: str,
        project_type: ProjectType,
        version: int = 1,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProjectData:
        try:
            project_name = ProjectName(name)
            now = datetime.now(UTC)
            project = Project(
                entity_id=uuid4(),
                user_id=identity.user_id,
                name=project_name,
                description=description,
                project_type=project_type,
                status=ProjectStatus.ACTIVE,
                metadata=metadata,
                version=version,
                created_at=now,
                updated_at=now,
            )
        except InvalidProject as error:
            raise InvalidInput(str(error)) from error

        await self._project_repository.create(project=project)

        return ProjectData(
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
