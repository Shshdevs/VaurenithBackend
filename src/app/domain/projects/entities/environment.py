from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.common.entity import Entity
from app.domain.common.slug import make_slug
from app.domain.common.types import EntityId
from app.domain.projects.enums import EnvironmentType
from app.domain.projects.exceptions import InvalidEnvironment
from app.domain.projects.value_objects import EnvironmentName


class Environment(Entity):
    MAX_NAME_LENGTH = EnvironmentName.MAX_LENGTH

    def __init__(
        self,
        entity_id: EntityId,
        project_id: EntityId,
        name: str,
        environment_type: EnvironmentType,
        description: str | None,
        configuration: dict[str, Any] | None,
        created_at: datetime,
        updated_at: datetime,
        version: int = 1,
        deleted_at: datetime | None = None,
    ) -> None:
        if not isinstance(entity_id, UUID) or not isinstance(project_id, UUID):
            raise InvalidEnvironment(
                "Environment and project identifiers must be UUIDs"
            )
        normalized_name = EnvironmentName(name)

        if not isinstance(environment_type, EnvironmentType):
            raise InvalidEnvironment("Environment type is invalid")

        if description is not None and not isinstance(description, str):
            raise InvalidEnvironment("Environment description must be a string")

        if configuration is not None and not isinstance(configuration, dict):
            raise InvalidEnvironment("Environment configuration must be a JSON object")

        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidEnvironment("Environment version must be a positive integer")

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidEnvironment("Update time cannot precede environment creation")
        if deleted_at is not None:
            self._validate_timestamp(deleted_at, "deleted_at")
            if deleted_at < created_at:
                raise InvalidEnvironment(
                    "Deletion time cannot precede environment creation"
                )
            if updated_at > deleted_at:
                raise InvalidEnvironment(
                    "Update time cannot follow environment deletion"
                )

        super().__init__(entity_id)
        self._project_id = project_id
        self._name = normalized_name
        self._environment_type = environment_type
        self._description = description
        self._configuration = deepcopy(configuration)
        self._created_at = created_at
        self._updated_at = updated_at
        self._version = version
        self._deleted_at = deleted_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidEnvironment(f"Environment {name} must include a timezone")

    @property
    def project_id(self) -> EntityId:
        return self._project_id

    @property
    def name(self) -> str:
        return self._name.value

    @property
    def name_value(self) -> EnvironmentName:
        return self._name

    @property
    def slug(self) -> str:
        return make_slug(self.name, f"environment-{self.id.hex[:8]}")

    @property
    def environment_type(self) -> EnvironmentType:
        return self._environment_type

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def configuration(self) -> dict[str, Any] | None:
        return deepcopy(self._configuration)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at
