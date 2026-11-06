from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.enums import EntityType
from app.domain.common.types import EntityId
from app.domain.synchronization.enums import ChangeOperation
from app.domain.synchronization.exceptions import InvalidChangeLog


class ChangeLog(Entity):
    """Ordered change feed for incremental synchronization.
    Payloads must exclude secrets."""

    MAX_VERSION = 2**63 - 1

    def __init__(
        self,
        change_log_id: EntityId,
        user_id: EntityId,
        entity_type: EntityType,
        entity_id: EntityId,
        operation: ChangeOperation,
        version: int,
        changed_by_user_id: EntityId,
        created_at: datetime,
        changed_by_client_id: EntityId | None = None,
        payload: Any | None = None,
    ) -> None:
        for identifier, name in (
            (change_log_id, "change log"),
            (user_id, "user"),
            (entity_id, "changed entity"),
            (changed_by_user_id, "actor user"),
        ):
            if not isinstance(identifier, UUID):
                raise InvalidChangeLog(f"{name.capitalize()} identifier must be a UUID")
        if changed_by_client_id is not None and not isinstance(
            changed_by_client_id, UUID
        ):
            raise InvalidChangeLog("Actor client identifier must be a UUID")
        if not isinstance(entity_type, EntityType):
            raise InvalidChangeLog("Entity type is invalid")
        if not isinstance(operation, ChangeOperation):
            raise InvalidChangeLog("Change operation is invalid")
        if (
            not isinstance(version, int)
            or isinstance(version, bool)
            or not 1 <= version <= self.MAX_VERSION
        ):
            raise InvalidChangeLog("Change version must be a positive 64-bit integer")
        if not isinstance(created_at, datetime) or created_at.utcoffset() is None:
            raise InvalidChangeLog("Change creation time must include a timezone")

        super().__init__(change_log_id)
        self._user_id = user_id
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._operation = operation
        self._version = version
        self._changed_by_client_id = changed_by_client_id
        self._changed_by_user_id = changed_by_user_id
        self._payload = deepcopy(payload)
        self._created_at = created_at

    @property
    def user_id(self) -> EntityId:
        return self._user_id

    @property
    def entity_type(self) -> EntityType:
        return self._entity_type

    @property
    def entity_id(self) -> EntityId:
        return self._entity_id

    @property
    def operation(self) -> ChangeOperation:
        return self._operation

    @property
    def version(self) -> int:
        return self._version

    @property
    def changed_by_client_id(self) -> EntityId | None:
        return self._changed_by_client_id

    @property
    def changed_by_user_id(self) -> EntityId:
        return self._changed_by_user_id

    @property
    def payload(self) -> Any | None:
        return deepcopy(self._payload)

    @property
    def created_at(self) -> datetime:
        return self._created_at
