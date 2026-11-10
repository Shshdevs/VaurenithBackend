from uuid import UUID

from app.application.identity.dto import VerifiedIdentity
from app.application.projects.exceptions import ProjectNotFound
from app.application.projects.interfaces import ProjectRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteProject:
    def __init__(
        self, project_repository: ProjectRepository, recorder: ChangeRecorder
    ) -> None:
        self._project_repository = project_repository
        self._recorder = recorder

    async def execute(self, identity: VerifiedIdentity, project_id: UUID) -> None:
        existing = await self._project_repository.get_by_id(identity.user_id, project_id)
        if existing is None:
            raise ProjectNotFound(str(project_id))
        result = await self._project_repository.delete(
            identity.user_id, project_id=project_id
        )
        if not result:
            raise ProjectNotFound(str(project_id))
        await self._recorder.execute(
            identity,
            EntityType.PROJECT,
            project_id,
            ChangeOperation.DELETE,
            existing.version + 1,
        )
