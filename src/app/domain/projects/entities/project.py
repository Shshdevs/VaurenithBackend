from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from ...common.entity import Entity
from ...common.types import EntityId
from ..enums import ProjectStatus, ProjectType
from ..exceptions import InvalidProject
from ..value_objects import ProjectName


class Project(Entity):
    """Central domain entity connecting development and infrastructure"""

    MAX_NAME_LENGTH = ProjectName.MAX_LENGTH

    def __init__(
        self,
        entity_id: EntityId,
        user_id: EntityId,
        name: str,
        created_at: datetime,
        updated_at: datetime,
        description: str | None = None,
        project_type: ProjectType = ProjectType.OTHER,
        status: ProjectStatus = ProjectStatus.ACTIVE,
        metadata: dict[str, Any] | None = None,
        version: int = 1,
        deleted_at: datetime | None = None,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(user_id, UUID):
            raise InvalidProject("Project and owner identifiers must be UUIDs")
        normalized_name = ProjectName(name)
        if description is not None and not isinstance(description, str):
            raise InvalidProject("Project description must be a string")
        if not isinstance(project_type, ProjectType):
            raise InvalidProject("Project type is invalid")
        if not isinstance(status, ProjectStatus):
            raise InvalidProject("Project status is invalid")
        if metadata is not None and not isinstance(metadata, dict):
            raise InvalidProject("Project metadata must be a JSON object")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidProject("Project version must be a positive integer")

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidProject("Last update time cannot precede project creation")
        if deleted_at is not None:
            self._validate_timestamp(deleted_at, "deleted_at")
            if deleted_at < created_at:
                raise InvalidProject("Deletion time cannot precede project creation")
            if updated_at > deleted_at:
                raise InvalidProject("Update time cannot follow project deletion")

        super().__init__(entity_id)
        self._user_id = user_id
        self._name = normalized_name
        self._description = description
        self._created_at = created_at
        self._updated_at = updated_at
        self._project_type = project_type
        self._status = status
        self._metadata = deepcopy(metadata)
        self._version = version
        self._deleted_at = deleted_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidProject(f"Project {name} must include a timezone")

    @property
    def user_id(self) -> EntityId:
        return self._user_id

    @property
    def name(self) -> str:
        return self._name.value

    @property
    def name_value(self) -> ProjectName:
        return self._name

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def project_type(self) -> ProjectType:
        return self._project_type

    @property
    def status(self) -> ProjectStatus:
        return self._status

    @property
    def metadata(self) -> dict[str, Any] | None:
        return deepcopy(self._metadata)

    @property
    def version(self) -> int:
        return self._version

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at
