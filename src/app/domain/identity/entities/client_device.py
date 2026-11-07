from datetime import datetime

from app.domain.common.entity import Entity
from app.domain.common.slug import make_slug
from app.domain.common.types import EntityId
from app.domain.identity.enums import ClientDeviceStatus, PlatformType
from app.domain.identity.exceptions import InvalidClientDevice


class ClientDevice(Entity):
    """Devices running Vaurenith client applications"""

    MAX_NAME_LENGTH = 255
    MAX_APP_VERSION_LENGTH = 50

    def __init__(
        self,
        entity_id: EntityId,
        user_id: EntityId,
        name: str,
        platform: PlatformType,
        registered_at: datetime,
        app_version: str | None = None,
        status: ClientDeviceStatus = ClientDeviceStatus.ACTIVE,
        last_seen_at: datetime | None = None,
        revoked_at: datetime | None = None,
    ) -> None:
        normalized_name = name.strip()
        if not normalized_name or len(normalized_name) > self.MAX_NAME_LENGTH:
            raise InvalidClientDevice("Device name is invalid")
        if app_version is not None and len(app_version) > self.MAX_APP_VERSION_LENGTH:
            raise InvalidClientDevice("App version is too long")

        self._validate_timestamp(registered_at, "registered_at")
        if last_seen_at is not None:
            self._validate_timestamp(last_seen_at, "last_seen_at")
            if last_seen_at < registered_at:
                raise InvalidClientDevice(
                    "Last seen time cannot precede device registration"
                )
        if revoked_at is not None:
            self._validate_timestamp(revoked_at, "revoked_at")
            if revoked_at < registered_at:
                raise InvalidClientDevice(
                    "Revocation time cannot precede device registration"
                )
        if (status is ClientDeviceStatus.REVOKED) != (revoked_at is not None):
            raise InvalidClientDevice(
                "Revoked status and revocation time must be set together"
            )
        if (
            revoked_at is not None
            and last_seen_at is not None
            and last_seen_at > revoked_at
        ):
            raise InvalidClientDevice("Last seen time cannot follow device revocation")

        super().__init__(entity_id)
        self._user_id = user_id
        self._name = normalized_name
        self._platform = platform
        self._app_version = app_version
        self._status = status
        self._registered_at = registered_at
        self._last_seen_at = last_seen_at
        self._revoked_at = revoked_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if value.utcoffset() is None:
            raise InvalidClientDevice(f"Device {name} must include a timezone")

    @property
    def user_id(self) -> EntityId:
        return self._user_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def slug(self) -> str:
        return make_slug(self.name, f"device-{self.id.hex[:8]}")

    @property
    def platform(self) -> PlatformType:
        return self._platform

    @property
    def app_version(self) -> str | None:
        return self._app_version

    @property
    def status(self) -> ClientDeviceStatus:
        return self._status

    @property
    def registered_at(self) -> datetime:
        return self._registered_at

    @property
    def last_seen_at(self) -> datetime | None:
        return self._last_seen_at

    @property
    def revoked_at(self) -> datetime | None:
        return self._revoked_at

    @property
    def is_active(self) -> bool:
        return self._status is ClientDeviceStatus.ACTIVE

    def mark_seen(self, at: datetime) -> None:
        self._validate_timestamp(at, "last seen time")
        if not self.is_active:
            raise InvalidClientDevice("Only active devices can be marked as seen")
        if at < self._registered_at:
            raise InvalidClientDevice("Last seen time cannot precede registration")
        if self._last_seen_at is not None and at < self._last_seen_at:
            raise InvalidClientDevice("Last seen time cannot move backwards")
        self._last_seen_at = at

    def deactivate(self) -> None:
        if self._status is ClientDeviceStatus.REVOKED:
            raise InvalidClientDevice("A revoked device cannot be deactivated")
        self._status = ClientDeviceStatus.INACTIVE

    def activate(self) -> None:
        if self._status is ClientDeviceStatus.REVOKED:
            raise InvalidClientDevice("A revoked device cannot be reactivated")
        self._status = ClientDeviceStatus.ACTIVE

    def revoke(self, at: datetime) -> None:
        self._validate_timestamp(at, "revocation time")
        if at < self._registered_at:
            raise InvalidClientDevice("Revocation cannot precede registration")
        if self._status is ClientDeviceStatus.REVOKED:
            return
        if self._last_seen_at is not None and self._last_seen_at > at:
            raise InvalidClientDevice("Revocation cannot precede the last seen time")
        self._status = ClientDeviceStatus.REVOKED
        self._revoked_at = at
