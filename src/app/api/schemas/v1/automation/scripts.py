from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.automation.enums import (
    ScriptExecutionType,
    ScriptRiskLevel,
)


class ScriptData(Schema):
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


class ScriptCreateRequest(Schema):
    project_id: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    content: str = Field(min_length=1)
    interpreter: str | None = Field(default=None, max_length=100)
    execution_type: ScriptExecutionType
    parameters: Any | None = None
    risk_level: ScriptRiskLevel = ScriptRiskLevel.SAFE
    requires_confirmation: bool = False


class ScriptUpdateRequest(ScriptCreateRequest):
    version: int = Field(ge=1, le=2**63 - 2)
