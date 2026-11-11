from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.automation.enums import ScriptExecutionType, ScriptRiskLevel


@dataclass(frozen=True, slots=True)
class ScriptData:
    id: UUID
    project_id: UUID | None
    name: str
    slug: str
    description: str | None
    content: str
    interpreter: str | None
    execution_type: ScriptExecutionType
    parameters: Any | None
    risk_level: ScriptRiskLevel
    requires_confirmation: bool
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def from_script(cls, script) -> "ScriptData":
        return cls(
            id=script.id,
            project_id=script.project_id,
            name=script.name,
            slug=script.slug,
            description=script.description,
            content=script.content,
            interpreter=script.interpreter,
            execution_type=script.execution_type,
            parameters=script.parameters,
            risk_level=script.risk_level,
            requires_confirmation=script.requires_confirmation,
            version=script.version,
            created_at=script.created_at,
            updated_at=script.updated_at,
            deleted_at=script.deleted_at,
        )
