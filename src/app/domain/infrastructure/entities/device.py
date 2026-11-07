from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.slug import make_slug
from app.domain.common.types import EntityId
from app.domain.infrastructure.enums import DeviceType
from app.domain.infrastructure.exceptions import InvalidDevice
from app.domain.infrastructure.value_objects import DeviceName, OperatingSystem


class Device(Entity):
    """Physical machines, virtual machines, VPS and other managed nodes"""

    MAX_ARCHITECTURE_LENGTH = 50
    MAX_OS_VERSION_LENGTH = 100
    MAX_OPERATING_SYSTEM_LENGTH = 100
    MAX_HOST_NAME_LENGTH = 255
    MAX_NAME_LENGTH = 255

    def __init__(
        self,
        entity_id: EntityId,
        user_id: EntityId,
        name: str,
        created_at: datetime,
        updated_at: datetime,
        device_type: DeviceType,
        hostname: str | None = None,
        description: str | None = None,
        operating_system: str | None = None,
        os_version: str | None = None,
        architecture: str | None = None,
        tags: list[str] | None = None,
        version: int = 1,
        last_seen_at: datetime | None = None,
        last_status_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(user_id, UUID):
            raise InvalidDevice("Device and owner identifiers must be UUIDs")
        normalized_name = DeviceName(name)
        if not isinstance(device_type, DeviceType):
            raise InvalidDevice("Device type is invalid")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidDevice("Device version must be a positive integer")

        normalized_hostname = self._normalize_optional_text(
            hostname, "hostname", self.MAX_HOST_NAME_LENGTH
        )
        normalized_description = self._normalize_optional_text(
            description, "description"
        )
        normalized_operating_system = self._normalize_optional_text(
            operating_system, "operating_system", self.MAX_OPERATING_SYSTEM_LENGTH
        )
        normalized_os_version = self._normalize_optional_text(
            os_version, "os_version", self.MAX_OS_VERSION_LENGTH
        )
        normalized_architecture = self._normalize_optional_text(
            architecture, "architecture", self.MAX_ARCHITECTURE_LENGTH
        )
        operating_system_info = None
        if any(
            value is not None
            for value in (
                normalized_operating_system,
                normalized_os_version,
                normalized_architecture,
            )
        ):
            operating_system_info = OperatingSystem(
                name=normalized_operating_system,
                version=normalized_os_version,
                architecture=normalized_architecture,
            )
        normalized_tags = self._normalize_tags(tags)

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidDevice("Update time cannot precede device creation")
        for timestamp, field_name in (
            (last_seen_at, "last_seen_at"),
            (last_status_at, "last_status_at"),
        ):
            if timestamp is not None:
                self._validate_timestamp(timestamp, field_name)
                if timestamp < created_at:
                    raise InvalidDevice(f"Device {field_name} cannot precede creation")
        if deleted_at is not None:
            self._validate_timestamp(deleted_at, "deleted_at")
            if deleted_at < created_at:
                raise InvalidDevice("Deletion time cannot precede device creation")
            if updated_at > deleted_at:
                raise InvalidDevice("Update time cannot follow device deletion")
            if last_seen_at is not None and last_seen_at > deleted_at:
                raise InvalidDevice("Last seen time cannot follow device deletion")
            if last_status_at is not None and last_status_at > deleted_at:
                raise InvalidDevice("Last status time cannot follow device deletion")

        super().__init__(entity_id)
        self._user_id = user_id
        self._name = normalized_name
        self._hostname = normalized_hostname
        self._description = normalized_description
        self._device_type = device_type
        self._operating_system_info = operating_system_info
        self._tags = normalized_tags
        self._version = version
        self._last_seen_at = last_seen_at
        self._last_status_at = last_status_at
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @staticmethod
    def _normalize_optional_text(
        value: str | None,
        name: str,
        max_length: int | None = None,
    ) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidDevice(f"Device {name} must be a string")
        normalized_value = value.strip()
        if not normalized_value:
            return None
        if max_length is not None and len(normalized_value) > max_length:
            raise InvalidDevice(f"Device {name} is too long")
        return normalized_value

    @staticmethod
    def _normalize_tags(tags: list[str] | None) -> list[str] | None:
        if tags is None:
            return None
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            raise InvalidDevice("Device tags must be a list of strings")
        normalized_tags = [tag.strip() for tag in tags]
        if any(not tag for tag in normalized_tags):
            raise InvalidDevice("Device tags cannot be empty")
        return normalized_tags

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidDevice(f"Device {name} must include a timezone")

    @property
    def user_id(self) -> EntityId:
        return self._user_id

    @property
    def name(self) -> str:
        return self._name.value

    @property
    def name_value(self) -> DeviceName:
        return self._name

    @property
    def slug(self) -> str:
        return make_slug(self.name, f"device-{self.id.hex[:8]}")

    @property
    def hostname(self) -> str | None:
        return self._hostname

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def device_type(self) -> DeviceType:
        return self._device_type

    @property
    def operating_system(self) -> str | None:
        return (
            self._operating_system_info.name
            if self._operating_system_info is not None
            else None
        )

    @property
    def os_version(self) -> str | None:
        return (
            self._operating_system_info.version
            if self._operating_system_info is not None
            else None
        )

    @property
    def architecture(self) -> str | None:
        return (
            self._operating_system_info.architecture
            if self._operating_system_info is not None
            else None
        )

    @property
    def operating_system_info(self) -> OperatingSystem | None:
        return self._operating_system_info

    @property
    def tags(self) -> list[str] | None:
        return self._tags.copy() if self._tags is not None else None

    @property
    def version(self) -> int:
        return self._version

    @property
    def last_seen_at(self) -> datetime | None:
        return self._last_seen_at

    @property
    def last_status_at(self) -> datetime | None:
        return self._last_status_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at
