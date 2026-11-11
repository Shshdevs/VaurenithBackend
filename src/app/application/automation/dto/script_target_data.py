from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ScriptTargetData:
    id: UUID
    script_id: UUID
    device_id: UUID
    environment_id: UUID | None
    created_at: datetime

    @classmethod
    def from_target(cls, target) -> "ScriptTargetData":
        return cls(
            id=target.id,
            script_id=target.script_id,
            device_id=target.device_id,
            environment_id=target.environment_id,
            created_at=target.created_at,
        )
