from datetime import datetime
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.types import EntityId
from app.domain.projects.exceptions import InvalidProjectDeviceRelation
from app.domain.projects.value_objects import ProjectDeviceRole


class ProjectDevice(Entity):
    """Many-to-many association between projects and infrastructure devices"""

    MAX_ROLE_LENGTH = ProjectDeviceRole.MAX_LENGTH

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

        normalized_role = (
            None
            if role is None or (isinstance(role, str) and not role.strip())
            else ProjectDeviceRole(role)
        )
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
        return self._role.value if self._role is not None else None

    @property
    def role_value(self) -> ProjectDeviceRole | None:
        return self._role
