from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.slug import make_slug
from app.domain.common.types import EntityId
from app.domain.infrastructure.exceptions import InvalidDeviceGroup
from app.domain.infrastructure.value_objects import DeviceGroupName


class DeviceGroup(Entity):
    def __init__(
        self,
        entity_id: EntityId,
        user_id: EntityId,
        name: DeviceGroupName,
        created_at: datetime,
        updated_at: datetime,
        description: str | None = None,
        version: int = 1,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(user_id, UUID):
            raise InvalidDeviceGroup("Device group and owner identifiers must be UUIDs")
        if not isinstance(name, DeviceGroupName):
            raise InvalidDeviceGroup("Device group name must be a DeviceGroupName")
        if description is not None and not isinstance(description, str):
            raise InvalidDeviceGroup("Device group description must be a string")

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidDeviceGroup("Update time cannot precede device group creation")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidDeviceGroup("Device group version must be positive")

        normalized_description = description.strip() if description is not None else None
        if normalized_description == "":
            normalized_description = None
        super().__init__(entity_id)
        self._user_id = user_id
        self._name = name
        self._description = normalized_description
        self._created_at = created_at
        self._updated_at = updated_at
        self._version = version

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidDeviceGroup(f"Device group {name} must include a timezone")

    @property
    def user_id(self) -> EntityId:
        return self._user_id

    @property
    def name(self) -> str:
        return self._name.value

    @property
    def name_value(self) -> DeviceGroupName:
        return self._name

    @property
    def slug(self) -> str:
        return make_slug(self.name, f"device-group-{self.id.hex[:8]}")

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version
