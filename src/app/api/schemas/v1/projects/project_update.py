from typing import Any

from pydantic import Field, field_validator

from app.api.schemas.common import Schema
from app.domain.projects.enums import ProjectStatus, ProjectType
from app.domain.projects.exceptions import InvalidProject
from app.domain.projects.value_objects.project_name import ProjectName


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
