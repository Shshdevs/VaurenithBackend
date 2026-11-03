from datetime import datetime
from uuid import UUID

from ...common.entity import Entity
from ...common.types import EntityId
from ..exceptions import InvalidProjectDeviceRelation


class ProjectDevice(Entity):
    MAX_ROLE_LENGTH = 100

    def __init__(
        self,
        entity_id: EntityId,
        project_id: EntityId,
        device_id: EntityId,
        created_at: datetime,
        role: str | None = None,
    ) -> None:
        if not all(
            isinstance(identifier, UUID)
            for identifier in (entity_id, project_id, device_id)
        ):
            raise InvalidProjectDeviceRelation("Project and device IDs must be UUIDs")

        normalized_role = role.strip() if role is not None else None
        if normalized_role == "":
            normalized_role = None
        if normalized_role is not None and len(normalized_role) > self.MAX_ROLE_LENGTH:
            raise InvalidProjectDeviceRelation("Relation role is too long")
        if not isinstance(created_at, datetime) or created_at.utcoffset() is None:
            raise InvalidProjectDeviceRelation(
                "Relation creation time must include a timezone"
            )

        super().__init__(entity_id)
        self._project_id = project_id
        self._device_id = device_id
        self._created_at = created_at
        self._role = normalized_role

    @property
    def project_id(self) -> EntityId:
        return self._project_id

    @property
    def device_id(self) -> EntityId:
        return self._device_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def role(self) -> str | None:
        return self._role
