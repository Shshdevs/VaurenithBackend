from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.types import EntityId
from app.domain.preferences.enums import SettingScope
from app.domain.preferences.exceptions import InvalidSetting


class Setting(Entity):
    """Global settings synchronize across clients;
    client settings are device-specific"""

    MAX_KEY_LENGTH = 255
    MAX_VERSION = 2**63 - 1

    def __init__(
        self,
        entity_id: EntityId,
        user_id: EntityId,
        scope: SettingScope,
        key: str,
        created_at: datetime,
        updated_at: datetime,
        client_device_id: EntityId | None = None,
        value: Any | None = None,
        version: int = 1,
    ) -> None:
        for identifier, name in ((entity_id, "setting"), (user_id, "user")):
            if not isinstance(identifier, UUID):
                raise InvalidSetting(f"{name.capitalize()} identifier must be a UUID")
        if client_device_id is not None and not isinstance(client_device_id, UUID):
            raise InvalidSetting("Client device identifier must be a UUID")
        if not isinstance(scope, SettingScope):
            raise InvalidSetting("Setting scope is invalid")
        if scope is SettingScope.CLIENT and client_device_id is None:
            raise InvalidSetting("Client settings require a client device")
        if scope is SettingScope.GLOBAL and client_device_id is not None:
            raise InvalidSetting("Global settings cannot target a client device")
        if not isinstance(key, str) or len(key) > self.MAX_KEY_LENGTH:
            raise InvalidSetting("Setting key must be at most 255 characters")
        if (
            not isinstance(version, int)
            or isinstance(version, bool)
            or not 1 <= version <= self.MAX_VERSION
        ):
            raise InvalidSetting("Setting version must be a positive 64-bit integer")
        self._validate_timestamp(created_at, "creation")
        self._validate_timestamp(updated_at, "update")
        if updated_at < created_at:
            raise InvalidSetting("Setting update time cannot precede creation time")

        super().__init__(entity_id)
        self._user_id = user_id
        self._client_device_id = client_device_id
        self._scope = scope
        self._key = key
        self._value = deepcopy(value)
        self._version = version
        self._created_at = created_at
        self._updated_at = updated_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidSetting(f"Setting {name} time must include a timezone")

    @property
    def user_id(self) -> EntityId:
        return self._user_id

    @property
    def client_device_id(self) -> EntityId | None:
        return self._client_device_id

    @property
    def scope(self) -> SettingScope:
        return self._scope

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> Any | None:
        return deepcopy(self._value)

    @property
    def version(self) -> int:
        return self._version

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
