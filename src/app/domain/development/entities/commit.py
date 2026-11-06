from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.types import EntityId
from app.domain.development.exceptions import InvalidCommit
from app.domain.development.value_objects import CommitHash


class Commit(Entity):
    """Selective cache of Git commit metadata. Git remains the source of truth."""

    MAX_AUTHOR_NAME_LENGTH = 255
    MAX_AUTHOR_EMAIL_LENGTH = 320

    def __init__(
        self,
        entity_id: EntityId,
        repository_id: EntityId,
        hash: str,
        author_name: str | None = None,
        author_email: str | None = None,
        message: str | None = None,
        committed_at: datetime | None = None,
        changed_files: Any | None = None,
        cached_at: datetime | None = None,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(repository_id, UUID):
            raise InvalidCommit("Commit and repository identifiers must be UUIDs")
        commit_hash = CommitHash(hash)
        normalized_author_name = self._normalize_optional_text(
            author_name, "author_name", self.MAX_AUTHOR_NAME_LENGTH
        )
        normalized_author_email = self._normalize_optional_text(
            author_email, "author_email", self.MAX_AUTHOR_EMAIL_LENGTH
        )
        if message is not None and not isinstance(message, str):
            raise InvalidCommit("Commit message must be a string")

        if committed_at is not None:
            self._validate_timestamp(committed_at, "committed_at")
        if cached_at is not None:
            self._validate_timestamp(cached_at, "cached_at")

        super().__init__(entity_id)
        self._repository_id = repository_id
        self._hash = commit_hash
        self._author_name = normalized_author_name
        self._author_email = normalized_author_email
        self._message = message
        self._committed_at = committed_at
        self._changed_files = deepcopy(changed_files)
        self._cached_at = cached_at

    @staticmethod
    def _normalize_optional_text(
        value: str | None,
        name: str,
        max_length: int,
    ) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidCommit(f"Commit {name} must be a string")
        normalized_value = value.strip()
        if not normalized_value:
            return None
        if len(normalized_value) > max_length:
            raise InvalidCommit(f"Commit {name} is too long")
        return normalized_value

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidCommit(f"Commit {name} must include a timezone")

    @property
    def repository_id(self) -> EntityId:
        return self._repository_id

    @property
    def hash(self) -> str:
        return self._hash.value

    @property
    def hash_value(self) -> CommitHash:
        return self._hash

    @property
    def author_name(self) -> str | None:
        return self._author_name

    @property
    def author_email(self) -> str | None:
        return self._author_email

    @property
    def message(self) -> str | None:
        return self._message

    @property
    def committed_at(self) -> datetime | None:
        return self._committed_at

    @property
    def changed_files(self) -> Any | None:
        return deepcopy(self._changed_files)

    @property
    def cached_at(self) -> datetime | None:
        return self._cached_at
