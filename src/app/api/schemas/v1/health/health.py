from datetime import datetime
from typing import Literal

from app.api.schemas.common import Schema


class DependencyHealth(Schema):
    status: Literal["OK", "UNAVAILABLE"]
    message: str | None = None


class LivenessData(Schema):
    status: Literal["OK"]
    timestamp: datetime


class ReadinessData(Schema):
    status: Literal["OK", "UNAVAILABLE"]
    timestamp: datetime
    database: DependencyHealth
