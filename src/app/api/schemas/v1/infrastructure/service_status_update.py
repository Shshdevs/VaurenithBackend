from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.infrastructure.enums import ResourceStatus


class ServiceStatusUpdateRequest(Schema):
    version: int = Field(ge=1)
    status: ResourceStatus
