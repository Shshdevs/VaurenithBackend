from uuid import UUID

from pydantic import field_validator

from app.api.schemas.common import Schema
from app.domain.projects import InvalidProjectDevice, ProjectDeviceRole


class ProjectDeviceCreateRequest(Schema):
    project_id: UUID
    device_id: UUID
    role: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return ProjectDeviceRole(value).value
        except InvalidProjectDevice as error:
            raise ValueError(str(error)) from error
