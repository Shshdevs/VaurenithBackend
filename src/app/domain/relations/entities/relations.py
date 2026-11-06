from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.enums import EntityType, RelationOrigin, RelationType
from app.domain.common.types import EntityId
from app.domain.relations.exceptions import InvalidRelation
from app.domain.relations.value_objects import EntityReference, RelationConfidence


class Relation(Entity):
    """Polymorphic relations between domain entities.
    Entity references are validated by application logic."""

    def __init__(
        self,
        entity_id: EntityId,
        project_id: EntityId,
        source_entity_type: EntityType,
        source_entity_id: EntityId,
        target_entity_type: EntityType,
        target_entity_id: EntityId,
        relation_type: RelationType,
        origin: RelationOrigin,
        created_at: datetime,
        updated_at: datetime,
        confidence: Decimal | None = None,
        metadata: Any | None = None,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(project_id, UUID):
            raise InvalidRelation("Relation and project identifiers must be UUIDs")
        source_reference = EntityReference(source_entity_type, source_entity_id)
        target_reference = EntityReference(target_entity_type, target_entity_id)
        if not isinstance(relation_type, RelationType):
            raise InvalidRelation("Relation type is invalid")
        if not isinstance(origin, RelationOrigin):
            raise InvalidRelation("Relation origin is invalid")
        relation_confidence = (
            RelationConfidence(confidence) if confidence is not None else None
        )

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidRelation("Update time cannot precede relation creation")

        super().__init__(entity_id)
        self._project_id = project_id
        self._source_reference = source_reference
        self._target_reference = target_reference
        self._relation_type = relation_type
        self._origin = origin
        self._confidence = relation_confidence
        self._metadata = deepcopy(metadata)
        self._created_at = created_at
        self._updated_at = updated_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidRelation(f"Relation {name} must include a timezone")

    @property
    def project_id(self) -> EntityId:
        return self._project_id

    @property
    def source_entity_type(self) -> EntityType:
        return self._source_reference.entity_type

    @property
    def source_entity_id(self) -> EntityId:
        return self._source_reference.entity_id

    @property
    def source_reference(self) -> EntityReference:
        return self._source_reference

    @property
    def target_entity_type(self) -> EntityType:
        return self._target_reference.entity_type

    @property
    def target_entity_id(self) -> EntityId:
        return self._target_reference.entity_id

    @property
    def target_reference(self) -> EntityReference:
        return self._target_reference

    @property
    def relation_type(self) -> RelationType:
        return self._relation_type

    @property
    def origin(self) -> RelationOrigin:
        return self._origin

    @property
    def confidence(self) -> Decimal | None:
        return self._confidence.value if self._confidence is not None else None

    @property
    def confidence_value(self) -> RelationConfidence | None:
        return self._confidence

    @property
    def metadata(self) -> Any | None:
        return deepcopy(self._metadata)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
