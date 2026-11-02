from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response, status

from ....application.monitoring.use_cases.check_database_health import (
    CheckDatabaseHealth,
)
from ...dependencies.container import get_database_health_check
from ...schemas.response import ApiResponse
from ...schemas.v1.health import DependencyHealth, LivenessData, ReadinessData

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[LivenessData])
def liveness() -> ApiResponse[LivenessData]:
    return ApiResponse[LivenessData](
        message="Service is healthy",
        data=LivenessData(status="OK", timestamp=datetime.now(UTC)),
    )


@router.get("/health/ready", response_model=ApiResponse[ReadinessData])
def readiness(
    response: Response,
    health_check: CheckDatabaseHealth = Depends(get_database_health_check),
) -> ApiResponse[ReadinessData]:
    database_available = health_check.execute()
    if not database_available:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        database = DependencyHealth(
            status="UNAVAILABLE",
            message="Database connection failed",
        )
        return ApiResponse[ReadinessData](
            message="Service unavailable",
            data=ReadinessData(
                status="UNAVAILABLE",
                timestamp=datetime.now(UTC),
                database=database,
            ),
        )

    return ApiResponse[ReadinessData](
        message="Service is ready",
        data=ReadinessData(
            status="OK",
            timestamp=datetime.now(UTC),
            database=DependencyHealth(status="OK", message="Database is ready"),
        ),
    )
