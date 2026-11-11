from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.development.enums import ComponentType


@dataclass(frozen=True, slots=True)
class CodeComponentData:
    id: UUID
    repository_id: UUID
    parent_id: UUID | None
    name: str
    path: str
    component_type: ComponentType
    language: str | None
    symbol: str | None
    start_line: int | None
    end_line: int | None
    analysis_version: str | None
    analyzed_at: datetime | None
    source_commit_hash: str | None
    created_at: datetime
    updated_at: datetime
    version: int

    @classmethod
    def from_component(cls, component) -> "CodeComponentData":
        return cls(
            id=component.id,
            repository_id=component.repository_id,
            parent_id=component.parent_id,
            name=component.name,
            path=component.path,
            component_type=component.component_type,
            language=component.language,
            symbol=component.symbol,
            start_line=component.start_line,
            end_line=component.end_line,
            analysis_version=component.analysis_version,
            analyzed_at=component.analyzed_at,
            source_commit_hash=component.source_commit_hash,
            created_at=component.created_at,
            updated_at=component.updated_at,
            version=component.version,
        )
