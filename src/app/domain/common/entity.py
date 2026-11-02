from .types import EntityId


class Entity:
    def __init__(self, entity_id: EntityId) -> None:
        self._id = entity_id

    @property
    def id(self) -> EntityId:
        return self._id

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other) or not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
