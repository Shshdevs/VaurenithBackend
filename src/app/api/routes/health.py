from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.schemas.health import DependencyHealth, LivenessData, ReadinessData
from app.api.schemas.response import ApiResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[LivenessData])
def liveness() -> ApiResponse[LivenessData]:
    return ApiResponse[LivenessData](
        message="OK",
        data=LivenessData(status="OK"),
    )


@router.get("/health/ready", response_model=ApiResponse[ReadinessData])
def readiness(
    response: Response,
    session: Session = Depends(get_db),
) -> ApiResponse[ReadinessData]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        database = DependencyHealth(
            status="UNAVAILABLE",
            message="Database connection failed",
        )
        return ApiResponse[ReadinessData](
            message="Service unavailable",
            data=ReadinessData(status="UNAVAILABLE", database=database),
        )

    return ApiResponse[ReadinessData](
        message="OK",
        data=ReadinessData(
            status="OK",
            database=DependencyHealth(status="OK"),
        ),
    )
