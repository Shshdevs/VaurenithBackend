from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.dto import RepositoryData
from app.application.development.interfaces import RepositoryRepository
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectNotFound
from app.application.projects.interfaces import ProjectRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.development.entities.repository import Repository
from app.domain.development.enums import RepositoryType
from app.domain.development.exceptions import InvalidRepository
from app.domain.synchronization import ChangeOperation


class CreateRepository:
    def __init__(
        self,
        repository_repository: RepositoryRepository,
        project_repository: ProjectRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository_repository = repository_repository
        self._project_repository = project_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def create_repository(
        self,
        identity: VerifiedIdentity,
        project_id: UUID,
        name: str,
        description: str | None,
        remote_url: str | None,
        default_branch: str | None,
        repository_type: RepositoryType,
    ) -> RepositoryData:
        project = await self._project_repository.get_by_id(identity.user_id, project_id)
        if project is None:
            raise ProjectNotFound(str(project_id))
        now = datetime.now(UTC)
        try:
            repository = Repository(
                entity_id=uuid4(),
                project_id=project_id,
                name=name,
                created_at=now,
                updated_at=now,
                description=description,
                remote_url=remote_url,
                default_branch=default_branch,
                repository_type=RepositoryType(repository_type),
            )
        except (InvalidRepository, ValueError) as error:
            raise InvalidInput(str(error)) from error
        await self._repository_repository.create(repository)
        await self._recorder.execute(
            identity,
            EntityType.REPOSITORY,
            repository.id,
            ChangeOperation.INSERT,
            repository.version,
            {
                "project_id": str(repository.project_id),
                "name": repository.name,
                "default_branch": repository.default_branch,
                "repository_type": repository.repository_type.value,
            },
        )
        return RepositoryData.from_repository(repository)
