from datetime import datetime
from uuid import UUID

from app.domain.automation.exceptions import InvalidScriptTarget
from app.domain.common.entity import Entity
from app.domain.common.types import EntityId


class ScriptTarget(Entity):
    """Many-to-many association between scripts and target devices or environments"""

    def __init__(
        self,
        entity_id: EntityId,
        script_id: EntityId,
        device_id: EntityId,
        created_at: datetime,
        environment_id: EntityId | None = None,
    ) -> None:
        if not all(
            isinstance(identifier, UUID) for identifier in (entity_id, script_id, device_id)
        ):
            raise InvalidScriptTarget(
                "Target, script, and device identifiers must be UUIDs"
            )
        if environment_id is not None and not isinstance(environment_id, UUID):
            raise InvalidScriptTarget("Environment identifier must be a UUID")
        if not isinstance(created_at, datetime) or created_at.utcoffset() is None:
            raise InvalidScriptTarget("Target creation time must include a timezone")

        super().__init__(entity_id)
        self._script_id = script_id
        self._device_id = device_id
        self._environment_id = environment_id
        self._created_at = created_at

    @property
    def script_id(self) -> EntityId:
        return self._script_id

    @property
    def device_id(self) -> EntityId:
        return self._device_id

    @property
    def environment_id(self) -> EntityId | None:
        return self._environment_id

    @property
    def created_at(self) -> datetime:
        return self._created_at
