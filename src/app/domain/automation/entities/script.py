from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.automation.enums import ScriptExecutionType, ScriptRiskLevel
from app.domain.automation.exceptions import InvalidScript
from app.domain.automation.value_objects import ScriptInterpreter, ScriptName
from app.domain.common.entity import Entity
from app.domain.common.slug import make_slug
from app.domain.common.types import EntityId


class Script(Entity):
    """Reusable local or remote scripts. Script content is synchronized as user data"""

    MAX_NAME_LENGTH = ScriptName.MAX_LENGTH
    MAX_INTERPRETER_LENGTH = ScriptInterpreter.MAX_LENGTH

    def __init__(
        self,
        entity_id: EntityId,
        name: str,
        content: str,
        execution_type: ScriptExecutionType,
        created_at: datetime,
        updated_at: datetime,
        project_id: EntityId | None = None,
        description: str | None = None,
        interpreter: str | None = None,
        parameters: Any | None = None,
        risk_level: ScriptRiskLevel = ScriptRiskLevel.SAFE,
        requires_confirmation: bool = False,
        version: int = 1,
        deleted_at: datetime | None = None,
    ) -> None:
        if not isinstance(entity_id, UUID):
            raise InvalidScript("Script identifier must be a UUID")
        if project_id is not None and not isinstance(project_id, UUID):
            raise InvalidScript("Project identifier must be a UUID")
        script_name = ScriptName(name)
        if not isinstance(content, str):
            raise InvalidScript("Script content must be a string")
        if description is not None and not isinstance(description, str):
            raise InvalidScript("Script description must be a string")
        script_interpreter = None
        if interpreter is not None and not (
            isinstance(interpreter, str) and not interpreter.strip()
        ):
            script_interpreter = ScriptInterpreter(interpreter)
        if not isinstance(execution_type, ScriptExecutionType):
            raise InvalidScript("Script execution type is invalid")
        if not isinstance(risk_level, ScriptRiskLevel):
            raise InvalidScript("Script risk level is invalid")
        if not isinstance(requires_confirmation, bool):
            raise InvalidScript("Requires confirmation must be a boolean")
        if (
            risk_level in (ScriptRiskLevel.DANGEROUS, ScriptRiskLevel.CRITICAL)
            and not requires_confirmation
        ):
            raise InvalidScript("Dangerous scripts require confirmation")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise InvalidScript("Script version must be a positive integer")

        self._validate_timestamp(created_at, "created_at")
        self._validate_timestamp(updated_at, "updated_at")
        if updated_at < created_at:
            raise InvalidScript("Update time cannot precede script creation")
        if deleted_at is not None:
            self._validate_timestamp(deleted_at, "deleted_at")
            if deleted_at < created_at:
                raise InvalidScript("Deletion time cannot precede script creation")
            if updated_at > deleted_at:
                raise InvalidScript("Update time cannot follow script deletion")

        super().__init__(entity_id)
        self._project_id = project_id
        self._name = script_name
        self._description = description
        self._content = content
        self._interpreter = script_interpreter
        self._execution_type = execution_type
        self._parameters = deepcopy(parameters)
        self._risk_level = risk_level
        self._requires_confirmation = requires_confirmation
        self._version = version
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidScript(f"Script {name} must include a timezone")

    @property
    def project_id(self) -> EntityId | None:
        return self._project_id

    @property
    def name(self) -> str:
        return self._name.value

    @property
    def slug(self) -> str:
        return make_slug(self.name, f"script-{self.id.hex[:8]}")

    @property
    def name_value(self) -> ScriptName:
        return self._name

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def content(self) -> str:
        return self._content

    @property
    def interpreter(self) -> str | None:
        return self._interpreter.value if self._interpreter is not None else None

    @property
    def interpreter_value(self) -> ScriptInterpreter | None:
        return self._interpreter

    @property
    def execution_type(self) -> ScriptExecutionType:
        return self._execution_type

    @property
    def parameters(self) -> Any | None:
        return deepcopy(self._parameters)

    @property
    def risk_level(self) -> ScriptRiskLevel:
        return self._risk_level

    @property
    def requires_confirmation(self) -> bool:
        return self._requires_confirmation

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
