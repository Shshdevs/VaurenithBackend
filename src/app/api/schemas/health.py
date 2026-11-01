from typing import Literal

from app.api.schemas.common import Schema


class DependencyHealth(Schema):
    status: Literal["OK", "UNAVAILABLE"]
    message: str | None = None


class LivenessData(Schema):
    status: Literal["OK"]


class ReadinessData(Schema):
    status: Literal["OK", "UNAVAILABLE"]
    database: DependencyHealth
