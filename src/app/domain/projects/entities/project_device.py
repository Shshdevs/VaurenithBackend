from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.types import EntityId
from app.domain.projects.exceptions import InvalidProjectDevice
from app.domain.projects.value_objects import ProjectDeviceRole


class ProjectDevice(Entity):
    """Many-to-many association between projects and infrastructure devices"""

    def __init__(
        self,
        entity_id: EntityId,
        project_id: EntityId,
        device_id: EntityId,
        created_at: datetime,
        role: ProjectDeviceRole | None = None,
    ) -> None:
        if not all(
            isinstance(identifier, UUID)
            for identifier in (entity_id, project_id, device_id)
        ):
            raise InvalidProjectDevice("Project and device IDs must be UUIDs")

        if not isinstance(created_at, datetime) or created_at.utcoffset() is None:
            raise InvalidProjectDevice("Relation creation time must include a timezone")

        super().__init__(entity_id)
        self._project_id = project_id
        self._device_id = device_id
        self._created_at = created_at
        self._role = role

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
        return self._role.value if self._role is not None else None

    @property
    def role_value(self) -> ProjectDeviceRole | None:
        return self._role
