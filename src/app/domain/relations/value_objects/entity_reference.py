from dataclasses import dataclass
from uuid import UUID

from ...common.enums import EntityType
from ...common.types import EntityId
from ...common.value_object import ValueObject
from ..exceptions import InvalidRelation


@dataclass(frozen=True, slots=True, eq=False)
class EntityReference(ValueObject):
    entity_type: EntityType
    entity_id: EntityId

    def __post_init__(self) -> None:
        if not isinstance(self.entity_type, EntityType):
            raise InvalidRelation("Referenced entity type is invalid")
        if not isinstance(self.entity_id, UUID):
            raise InvalidRelation("Referenced entity identifier must be a UUID")

    def equality_components(self) -> tuple[EntityType | UUID, ...]:
        return (self.entity_type, self.entity_id)
