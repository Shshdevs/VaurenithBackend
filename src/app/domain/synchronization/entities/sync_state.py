from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.enums import EntityType
from app.domain.common.types import EntityId
from app.domain.synchronization.enums import SyncStatus
from app.domain.synchronization.exceptions import InvalidSyncState


class SyncState(Entity):
    """Tracks synchronization state.
    Entity-level rows are optional; device-level cursor is stored separately."""

    MAX_VERSION = 2**63 - 1

    def __init__(
        self,
        sync_state_id: EntityId,
        user_id: EntityId,
        client_device_id: EntityId,
        updated_at: datetime,
        entity_type: EntityType | None = None,
        entity_id: EntityId | None = None,
        local_version: int | None = None,
        server_version: int | None = None,
        status: SyncStatus = SyncStatus.PENDING,
        last_synced_at: datetime | None = None,
        last_error: str | None = None,
    ) -> None:
        for identifier, name in (
            (sync_state_id, "sync state"),
            (user_id, "user"),
            (client_device_id, "client device"),
        ):
            if not isinstance(identifier, UUID):
                raise InvalidSyncState(f"{name.capitalize()} identifier must be a UUID")
        if entity_type is not None and not isinstance(entity_type, EntityType):
            raise InvalidSyncState("Entity type is invalid")
        if (entity_type is None) != (entity_id is None):
            raise InvalidSyncState("Entity type and entity identifier must be set together")
        if entity_id is not None and not isinstance(entity_id, UUID):
            raise InvalidSyncState("Synchronized entity identifier must be a UUID")
        if not isinstance(status, SyncStatus):
            raise InvalidSyncState("Synchronization status is invalid")
        for version, name in ((local_version, "local"), (server_version, "server")):
            if version is not None and (
                not isinstance(version, int)
                or isinstance(version, bool)
                or not 0 <= version <= self.MAX_VERSION
            ):
                raise InvalidSyncState(
                    f"{name.capitalize()} version must be a non-negative 64-bit integer"
                )
        self._validate_timestamp(updated_at, "update")
        if last_synced_at is not None:
            self._validate_timestamp(last_synced_at, "last synchronization")
        if last_error is not None and not isinstance(last_error, str):
            raise InvalidSyncState("Last error must be a string")

        super().__init__(sync_state_id)
        self._user_id = user_id
        self._client_device_id = client_device_id
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._local_version = local_version
        self._server_version = server_version
        self._status = status
        self._last_synced_at = last_synced_at
        self._last_error = last_error
        self._updated_at = updated_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidSyncState(f"Synchronization {name} time must include a timezone")

    @property
    def user_id(self) -> EntityId:
        return self._user_id

    @property
    def client_device_id(self) -> EntityId:
        return self._client_device_id

    @property
    def entity_type(self) -> EntityType | None:
        return self._entity_type

    @property
    def entity_id(self) -> EntityId | None:
        return self._entity_id

    @property
    def local_version(self) -> int | None:
        return self._local_version

    @property
    def server_version(self) -> int | None:
        return self._server_version

    @property
    def status(self) -> SyncStatus:
        return self._status

    @property
    def last_synced_at(self) -> datetime | None:
        return self._last_synced_at

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
