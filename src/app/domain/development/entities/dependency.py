from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.enums import RelationOrigin
from app.domain.common.types import EntityId
from app.domain.development.enums import DependencyType
from app.domain.development.exceptions import InvalidDependency
from app.domain.development.value_objects import Confidence


class Dependency(Entity):
    """Directed or undirected dependencies between code components"""

    MAX_ANALYSIS_VERSION_LENGTH = 100

    def __init__(
        self,
        entity_id: EntityId,
        source_component_id: EntityId,
        target_component_id: EntityId,
        dependency_type: DependencyType,
        is_directed: bool = True,
        source_type: RelationOrigin = RelationOrigin.AUTOMATIC,
        confidence: Decimal | None = None,
        analysis_version: str | None = None,
        analyzed_at: datetime | None = None,
        metadata: Any | None = None,
    ) -> None:
        if not isinstance(entity_id, UUID):
            raise InvalidDependency("Dependency identifier must be a UUID")
        if not isinstance(source_component_id, UUID) or not isinstance(
            target_component_id, UUID
        ):
            raise InvalidDependency("Component identifiers must be UUIDs")
        if not isinstance(dependency_type, DependencyType):
            raise InvalidDependency("Dependency type is invalid")
        if not isinstance(is_directed, bool):
            raise InvalidDependency("Directed flag must be a boolean")
        if not isinstance(source_type, RelationOrigin):
            raise InvalidDependency("Dependency source type is invalid")

        confidence_value = Confidence(confidence) if confidence is not None else None
        normalized_analysis_version = self._normalize_analysis_version(analysis_version)
        if analyzed_at is not None:
            self._validate_timestamp(analyzed_at, "analyzed_at")

        super().__init__(entity_id)
        self._source_component_id = source_component_id
        self._target_component_id = target_component_id
        self._dependency_type = dependency_type
        self._is_directed = is_directed
        self._source_type = source_type
        self._confidence = confidence_value
        self._analysis_version = normalized_analysis_version
        self._analyzed_at = analyzed_at
        self._metadata = deepcopy(metadata)

    @classmethod
    def _normalize_analysis_version(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidDependency("Analysis version must be a string")
        normalized_value = value.strip()
        if not normalized_value:
            return None
        if len(normalized_value) > cls.MAX_ANALYSIS_VERSION_LENGTH:
            raise InvalidDependency("Analysis version is too long")
        return normalized_value

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidDependency(f"Dependency {name} must include a timezone")

    @property
    def source_component_id(self) -> EntityId:
        return self._source_component_id

    @property
    def target_component_id(self) -> EntityId:
        return self._target_component_id

    @property
    def dependency_type(self) -> DependencyType:
        return self._dependency_type

    @property
    def is_directed(self) -> bool:
        return self._is_directed

    @property
    def source_type(self) -> RelationOrigin:
        return self._source_type

    @property
    def confidence(self) -> Decimal | None:
        return self._confidence.value if self._confidence is not None else None

    @property
    def confidence_value(self) -> Confidence | None:
        return self._confidence

    @property
    def analysis_version(self) -> str | None:
        return self._analysis_version

    @property
    def analyzed_at(self) -> datetime | None:
        return self._analyzed_at

    @property
    def metadata(self) -> Any | None:
        return deepcopy(self._metadata)
