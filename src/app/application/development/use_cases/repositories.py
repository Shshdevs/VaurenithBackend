from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.dto import RepositoryData
from app.application.development.exceptions import (
    RepositoryNotFound,
    RepositoryVersionConflict,
)
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
        await self._record(identity, repository, ChangeOperation.INSERT)
        return RepositoryData.from_repository(repository)

    async def _record(
        self,
        identity: VerifiedIdentity,
        repository: Repository,
        operation: ChangeOperation,
    ) -> None:
        await self._recorder.execute(
            identity,
            EntityType.REPOSITORY,
            repository.id,
            operation,
            repository.version,
            {
                "project_id": str(repository.project_id),
                "name": repository.name,
                "default_branch": repository.default_branch,
                "repository_type": repository.repository_type.value,
            },
        )


class GetRepository:
    def __init__(self, repository_repository: RepositoryRepository) -> None:
        self._repository_repository = repository_repository

    async def get_repository(
        self, identity: VerifiedIdentity, repository_id: UUID
    ) -> RepositoryData:
        repository = await self._repository_repository.get_by_id(
            identity.user_id, repository_id
        )
        if repository is None:
            raise RepositoryNotFound(str(repository_id))
        return RepositoryData.from_repository(repository)


class GetUserRepositories:
    def __init__(self, repository_repository: RepositoryRepository) -> None:
        self._repository_repository = repository_repository

    async def get_user_repositories(
        self, identity: VerifiedIdentity
    ) -> list[RepositoryData]:
        repositories = await self._repository_repository.get_by_user(identity.user_id)
        return [RepositoryData.from_repository(repository) for repository in repositories]


class GetProjectRepositories:
    def __init__(
        self,
        repository_repository: RepositoryRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self._repository_repository = repository_repository
        self._project_repository = project_repository

    async def get_project_repositories(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[RepositoryData]:
        project = await self._project_repository.get_by_id(identity.user_id, project_id)
        if project is None:
            raise ProjectNotFound(str(project_id))
        repositories = await self._repository_repository.get_by_project(
            identity.user_id, project_id
        )
        return [RepositoryData.from_repository(repository) for repository in repositories]


class UpdateRepository:
    def __init__(
        self,
        repository_repository: RepositoryRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository_repository = repository_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def update_repository(
        self,
        identity: VerifiedIdentity,
        repository_id: UUID,
        expected_version: int,
        name: str,
        description: str | None,
        remote_url: str | None,
        default_branch: str | None,
        repository_type: RepositoryType,
    ) -> RepositoryData:
        existing = await self._repository_repository.get_by_id(
            identity.user_id, repository_id
        )
        if existing is None:
            raise RepositoryNotFound(str(repository_id))
        if existing.version != expected_version:
            raise RepositoryVersionConflict(expected_version, existing.version)
        try:
            repository = Repository(
                entity_id=existing.id,
                project_id=existing.project_id,
                name=name,
                created_at=existing.created_at,
                updated_at=datetime.now(UTC),
                description=description,
                remote_url=remote_url,
                default_branch=default_branch,
                repository_type=RepositoryType(repository_type),
                version=expected_version + 1,
            )
        except (InvalidRepository, ValueError) as error:
            raise InvalidInput(str(error)) from error
        if not await self._repository_repository.update(
            identity.user_id, repository, expected_version
        ):
            raise RepositoryVersionConflict(expected_version)
        await self._record(identity, repository, ChangeOperation.UPDATE)
        return RepositoryData.from_repository(repository)

    async def _record(
        self,
        identity: VerifiedIdentity,
        repository: Repository,
        operation: ChangeOperation,
    ) -> None:
        await self._recorder.execute(
            identity,
            EntityType.REPOSITORY,
            repository.id,
            operation,
            repository.version,
            {
                "project_id": str(repository.project_id),
                "name": repository.name,
                "default_branch": repository.default_branch,
                "repository_type": repository.repository_type.value,
            },
        )


class DeleteRepository:
    def __init__(
        self,
        repository_repository: RepositoryRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository_repository = repository_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def delete_repository(
        self,
        identity: VerifiedIdentity,
        repository_id: UUID,
        expected_version: int,
    ) -> None:
        existing = await self._repository_repository.get_by_id(
            identity.user_id, repository_id
        )
        if existing is None:
            raise RepositoryNotFound(str(repository_id))
        if existing.version != expected_version:
            raise RepositoryVersionConflict(expected_version, existing.version)
        if not await self._repository_repository.delete(
            identity.user_id, repository_id, expected_version
        ):
            raise RepositoryVersionConflict(expected_version)
        await self._recorder.execute(
            identity,
            EntityType.REPOSITORY,
            existing.id,
            ChangeOperation.DELETE,
            expected_version + 1,
            {"project_id": str(existing.project_id), "name": existing.name},
        )
