from datetime import datetime

from app.domain.common.entity import Entity
from app.domain.common.types import EntityId
from app.domain.identity.exceptions import InvalidSession
from app.domain.identity.value_objects.token_hash import TokenHash


class Session(Entity):
    """Cloud authentication sessions. Never store raw access tokens."""

    def __init__(
        self,
        entity_id: EntityId,
        user_id: EntityId,
        token_hash: TokenHash,
        expires_at: datetime,
        created_at: datetime,
        client_device_id: EntityId | None = None,
        revoked_at: datetime | None = None,
    ) -> None:
        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(expires_at, "expires_at")
        if expires_at <= created_at:
            raise InvalidSession("Session expiry must be after its creation")
        if revoked_at is not None:
            self._validate_timestamp(revoked_at, "revoked_at")
            if revoked_at < created_at:
                raise InvalidSession("Session cannot be revoked before its creation")
        super().__init__(entity_id)
        self._user_id = user_id
        self._client_device_id = client_device_id
        self._token_hash = token_hash
        self._expires_at = expires_at
        self._created_at = created_at
        self._revoked_at = revoked_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if value.utcoffset() is None:
            raise InvalidSession(f"Session {name} must include a timezone")

    @property
    def user_id(self) -> EntityId:
        return self._user_id

    @property
    def client_device_id(self) -> EntityId | None:
        return self._client_device_id

    @property
    def token_hash(self) -> TokenHash:
        return self._token_hash

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def revoked_at(self) -> datetime | None:
        return self._revoked_at

    def is_active(self, at: datetime) -> bool:
        self._validate_timestamp(at, "evaluation time")
        return self._revoked_at is None and at < self._expires_at

    def revoke(self, at: datetime) -> None:
        self._validate_timestamp(at, "revocation time")
        if at < self._created_at:
            raise InvalidSession("Session cannot be revoked before its creation")
        if self._revoked_at is None:
            self._revoked_at = at
