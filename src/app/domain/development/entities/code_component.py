from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.types import EntityId
from app.domain.development.enums import ComponentType
from app.domain.development.exceptions import InvalidCodeComponent
from app.domain.development.value_objects import (
    CommitHash,
    ComponentName,
    ComponentPath,
)


class CodeComponent(Entity):
    """Structural metadata of source code. Does not store complete source files."""

    MAX_LANGUAGE_LENGTH = 100
    MAX_SYMBOL_LENGTH = 512
    MAX_ANALYSIS_VERSION_LENGTH = 100

    def __init__(
        self,
        entity_id: EntityId,
        repository_id: EntityId,
        name: str,
        path: str,
        component_type: ComponentType,
        created_at: datetime,
        updated_at: datetime,
        parent_id: EntityId | None = None,
        language: str | None = None,
        symbol: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        analysis_version: str | None = None,
        analyzed_at: datetime | None = None,
        source_commit_hash: str | None = None,
        version: int = 1,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(repository_id, UUID):
            raise InvalidCodeComponent("Component and repository identifiers must be UUIDs")
        if parent_id is not None and not isinstance(parent_id, UUID):
            raise InvalidCodeComponent("Parent identifier must be a UUID")
        if parent_id == entity_id:
            raise InvalidCodeComponent("A code component cannot be its own parent")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidCodeComponent("Component version must be a positive integer")

        component_name = ComponentName(name)
        component_path = ComponentPath(path)
        if not isinstance(component_type, ComponentType):
            raise InvalidCodeComponent("Component type is invalid")
        normalized_language = self._normalize_optional_text(
            language, "language", self.MAX_LANGUAGE_LENGTH
        )
        normalized_symbol = self._normalize_optional_text(
            symbol, "symbol", self.MAX_SYMBOL_LENGTH
        )
        normalized_analysis_version = self._normalize_optional_text(
            analysis_version, "analysis_version", self.MAX_ANALYSIS_VERSION_LENGTH
        )
        if start_line is not None:
            self._validate_line_number(start_line, "start_line")
        if end_line is not None:
            self._validate_line_number(end_line, "end_line")
        if start_line is not None and end_line is not None and end_line < start_line:
            raise InvalidCodeComponent("End line cannot precede start line")
        commit_hash = (
            CommitHash(source_commit_hash) if source_commit_hash is not None else None
        )

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidCodeComponent("Update time cannot precede component creation")
        if analyzed_at is not None:
            self._validate_timestamp(analyzed_at, "analyzed_at")

        super().__init__(entity_id)
        self._repository_id = repository_id
        self._parent_id = parent_id
        self._name = component_name
        self._path = component_path
        self._component_type = component_type
        self._language = normalized_language
        self._symbol = normalized_symbol
        self._start_line = start_line
        self._end_line = end_line
        self._analysis_version = normalized_analysis_version
        self._analyzed_at = analyzed_at
        self._source_commit_hash = commit_hash
        self._created_at = created_at
        self._updated_at = updated_at
        self._version = version

    @staticmethod
    def _normalize_optional_text(
        value: str | None,
        name: str,
        max_length: int,
    ) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidCodeComponent(f"Component {name} must be a string")
        normalized_value = value.strip()
        if not normalized_value:
            return None
        if len(normalized_value) > max_length:
            raise InvalidCodeComponent(f"Component {name} is too long")
        return normalized_value

    @staticmethod
    def _validate_line_number(value: int, name: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise InvalidCodeComponent(f"Component {name} must be a positive integer")

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidCodeComponent(f"Component {name} must include a timezone")

    @property
    def repository_id(self) -> EntityId:
        return self._repository_id

    @property
    def parent_id(self) -> EntityId | None:
        return self._parent_id

    @property
    def name(self) -> str:
        return self._name.value

    @property
    def name_value(self) -> ComponentName:
        return self._name

    @property
    def path(self) -> str:
        return self._path.value

    @property
    def path_value(self) -> ComponentPath:
        return self._path

    @property
    def component_type(self) -> ComponentType:
        return self._component_type

    @property
    def language(self) -> str | None:
        return self._language

    @property
    def symbol(self) -> str | None:
        return self._symbol

    @property
    def start_line(self) -> int | None:
        return self._start_line

    @property
    def end_line(self) -> int | None:
        return self._end_line

    @property
    def analysis_version(self) -> str | None:
        return self._analysis_version

    @property
    def analyzed_at(self) -> datetime | None:
        return self._analyzed_at

    @property
    def source_commit_hash(self) -> str | None:
        return (
            self._source_commit_hash.value if self._source_commit_hash is not None else None
        )

    @property
    def source_commit_hash_value(self) -> CommitHash | None:
        return self._source_commit_hash

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version
