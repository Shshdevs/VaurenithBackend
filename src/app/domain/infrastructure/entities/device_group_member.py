from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.types import EntityId
from app.domain.infrastructure.exceptions import InvalidDeviceGroupMember


class DeviceGroupMember(Entity):
    def __init__(
        self,
        entity_id: EntityId,
        group_id: EntityId,
        device_id: EntityId,
        created_at: datetime,
    ) -> None:
        if not all(
            isinstance(identifier, UUID) for identifier in (entity_id, group_id, device_id)
        ):
            raise InvalidDeviceGroupMember(
                "Membership, group, and device identifiers must be UUIDs"
            )
        if not isinstance(created_at, datetime) or created_at.utcoffset() is None:
            raise InvalidDeviceGroupMember(
                "Membership creation time must include a timezone"
            )
        super().__init__(entity_id)
        self._group_id = group_id
        self._device_id = device_id
        self._created_at = created_at

    @property
    def group_id(self) -> EntityId:
        return self._group_id

    @property
    def device_id(self) -> EntityId:
        return self._device_id

    @property
    def created_at(self) -> datetime:
        return self._created_at
