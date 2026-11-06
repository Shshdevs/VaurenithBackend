from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.types import EntityId
from app.domain.development.enums import RepositoryType
from app.domain.development.exceptions import InvalidBranch, InvalidRepository
from app.domain.development.value_objects import (
    BranchName,
    RemoteRepositoryUrl,
    RepositoryName,
)


class Repository(Entity):
    """Repository metadata.
    Source code and complete Git history remain in Git repositories"""

    MAX_DEFAULT_BRANCH_LENGTH = BranchName.MAX_LENGTH
    MAX_NAME_LENGTH = RepositoryName.MAX_LENGTH

    def __init__(
        self,
        entity_id: EntityId,
        project_id: EntityId,
        name: str,
        created_at: datetime,
        updated_at: datetime,
        description: str | None = None,
        remote_url: str | None = None,
        default_branch: str | None = None,
        repository_type: RepositoryType = RepositoryType.GIT,
        version: int = 1,
        deleted_at: datetime | None = None,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(project_id, UUID):
            raise InvalidRepository("Repository and project identifiers must be UUIDs")
        repository_name = RepositoryName(name)
        normalized_remote_url = None
        if remote_url is not None and not (
            isinstance(remote_url, str) and not remote_url.strip()
        ):
            normalized_remote_url = RemoteRepositoryUrl(remote_url)
        normalized_default_branch = None
        if default_branch is not None and not (
            isinstance(default_branch, str) and not default_branch.strip()
        ):
            try:
                normalized_default_branch = BranchName(default_branch)
            except InvalidBranch as error:
                raise InvalidRepository("Default branch name is invalid") from error
        if description is not None and not isinstance(description, str):
            raise InvalidRepository("Repository description must be a string")
        if not isinstance(repository_type, RepositoryType):
            raise InvalidRepository("Repository type is invalid")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidRepository("Repository version must be a positive integer")

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidRepository("Update time cannot precede repository creation")
        if deleted_at is not None:
            self._validate_timestamp(deleted_at, "deleted_at")
            if deleted_at < created_at:
                raise InvalidRepository(
                    "Deletion time cannot precede repository creation"
                )
            if updated_at > deleted_at:
                raise InvalidRepository("Update time cannot follow repository deletion")

        super().__init__(entity_id)
        self._project_id = project_id
        self._name = repository_name
        self._description = description
        self._remote_url = normalized_remote_url
        self._default_branch = normalized_default_branch
        self._repository_type = repository_type
        self._version = version
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidRepository(f"Repository {name} must include a timezone")

    @property
    def project_id(self) -> EntityId:
        return self._project_id

    @property
    def name(self) -> str:
        return self._name.value

    @property
    def name_value(self) -> RepositoryName:
        return self._name

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def remote_url(self) -> str | None:
        return self._remote_url.value if self._remote_url is not None else None

    @property
    def remote_url_value(self) -> RemoteRepositoryUrl | None:
        return self._remote_url

    @property
    def default_branch(self) -> str | None:
        return self._default_branch.value if self._default_branch is not None else None

    @property
    def default_branch_value(self) -> BranchName | None:
        return self._default_branch

    @property
    def repository_type(self) -> RepositoryType:
        return self._repository_type

    @property
    def version(self) -> int:
        return self._version

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at
