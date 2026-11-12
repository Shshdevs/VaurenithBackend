from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.projects.enums import ProjectStatus, ProjectType
from app.domain.projects.exceptions import InvalidProject
from app.domain.projects.value_objects.project_name import ProjectName


class ProjectData(Schema):
    id: UUID
    user_id: UUID
    name: str
    slug: str
    description: str | None
    project_type: ProjectType
    status: ProjectStatus
    metadata: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> str:
        name = value.value if isinstance(value, ProjectName) else value
        if not isinstance(name, str):
            raise ValueError("Project name is invalid")
        try:
            return ProjectName(name).value
        except InvalidProject as error:
            raise ValueError(str(error)) from error


class ProjectCreateRequest(Schema):
    name: str
    project_type: ProjectType = ProjectType.OTHER
    version: int = Field(default=1, ge=1)
    description: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return ProjectName(value).value
        except InvalidProject as error:
            raise ValueError(str(error)) from error


class ProjectUpdateRequest(Schema):
    name: str
    project_type: ProjectType
    status: ProjectStatus
    version: int = Field(ge=1)
    description: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        try:
            return ProjectName(value).value
        except InvalidProject as error:
            raise ValueError(str(error)) from error
