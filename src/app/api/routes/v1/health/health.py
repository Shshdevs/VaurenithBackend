from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response, status

from app.api.schemas import ApiResponse, format_http_status
from app.api.schemas.v1 import DependencyHealth, LivenessData, ReadinessData
from app.application.health.use_cases import CheckDatabaseHealth


def build_health_router(
    health_check_dependency: Callable[..., CheckDatabaseHealth],
) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health", response_model=ApiResponse[LivenessData])
    def liveness() -> ApiResponse[LivenessData]:
        return ApiResponse[LivenessData](
            message="Service is healthy",
            status=format_http_status(status.HTTP_200_OK),
            data=LivenessData(status="OK", timestamp=datetime.now(UTC)),
        )

    @router.get("/health/ready", response_model=ApiResponse[ReadinessData])
    async def readiness(
        response: Response,
        health_check: CheckDatabaseHealth = Depends(health_check_dependency),
    ) -> ApiResponse[ReadinessData]:
        database_available = await health_check.execute()
        if not database_available:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            database = DependencyHealth(
                status="UNAVAILABLE",
                message="Database connection failed",
            )
            return ApiResponse[ReadinessData](
                message="Service unavailable",
                status=format_http_status(response.status_code),
                data=ReadinessData(
                    status="UNAVAILABLE",
                    timestamp=datetime.now(UTC),
                    database=database,
                ),
            )

        return ApiResponse[ReadinessData](
            message="Service is ready",
            status=format_http_status(status.HTTP_200_OK),
            data=ReadinessData(
                status="OK",
                timestamp=datetime.now(UTC),
                database=DependencyHealth(status="OK", message="Database is ready"),
            ),
        )

    return router
