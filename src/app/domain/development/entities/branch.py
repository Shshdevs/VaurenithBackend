from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.types import EntityId
from app.domain.development.exceptions import InvalidBranch
from app.domain.development.value_objects import BranchName, CommitHash


class Branch(Entity):
    """Cached Git branch metadata"""

    MAX_COMMIT_HASH_LENGTH = CommitHash.SHA256_LENGTH
    MAX_NAME_LENGTH = BranchName.MAX_LENGTH

    def __init__(
        self,
        entity_id: EntityId,
        repository_id: EntityId,
        name: str,
        last_updated_at: datetime | None = None,
        last_synced_at: datetime | None = None,
        commit_hash: str | None = None,
        is_remote: bool = False,
        is_current: bool = False,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(repository_id, UUID):
            raise InvalidBranch("Branch and repository identifiers must be UUIDs")
        branch_name = BranchName(name)
        normalized_commit_hash = (
            CommitHash(commit_hash) if commit_hash is not None else None
        )
        if not isinstance(is_remote, bool):
            raise InvalidBranch("Remote branch flag must be a boolean")
        if not isinstance(is_current, bool):
            raise InvalidBranch("Current branch flag must be a boolean")
        if last_updated_at is not None:
            self._validate_timestamp(last_updated_at, "last_updated_at")
        if last_synced_at is not None:
            self._validate_timestamp(last_synced_at, "last_synced_at")

        super().__init__(entity_id)
        self._repository_id = repository_id
        self._name = branch_name
        self._commit_hash = normalized_commit_hash
        self._is_remote = is_remote
        self._is_current = is_current
        self._last_updated_at = last_updated_at
        self._last_synced_at = last_synced_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidBranch(f"Branch {name} must include a timezone")

    @property
    def repository_id(self) -> EntityId:
        return self._repository_id

    @property
    def name(self) -> str:
        return self._name.value

    @property
    def name_value(self) -> BranchName:
        return self._name

    @property
    def commit_hash(self) -> str | None:
        return self._commit_hash.value if self._commit_hash is not None else None

    @property
    def commit_hash_value(self) -> CommitHash | None:
        return self._commit_hash

    @property
    def is_remote(self) -> bool:
        return self._is_remote

    @property
    def is_current(self) -> bool:
        return self._is_current

    @property
    def last_updated_at(self) -> datetime | None:
        return self._last_updated_at

    @property
    def last_synced_at(self) -> datetime | None:
        return self._last_synced_at
