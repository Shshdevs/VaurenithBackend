from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.automation import Script
from app.domain.automation.enums import ScriptExecutionType, ScriptRiskLevel


@dataclass(frozen=True)
class ScriptChangeLogData:
    project_id: UUID | None
    execution_type: ScriptExecutionType
    risk_level: ScriptRiskLevel
    requires_confirmation: bool

    @classmethod
    def from_script(cls, script: Script) -> ScriptChangeLogData:
        return cls(
            project_id=script.project_id,
            execution_type=script.execution_type,
            risk_level=script.risk_level,
            requires_confirmation=script.requires_confirmation,
        )

    def to_payload(self) -> dict[str, str | bool | None]:
        return {
            "project_id": str(self.project_id) if self.project_id else None,
            "execution_type": self.execution_type.value,
            "risk_level": self.risk_level.value,
            "requires_confirmation": self.requires_confirmation,
        }
