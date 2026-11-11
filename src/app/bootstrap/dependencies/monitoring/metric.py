from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monitoring import CreateMetric, GetDeviceMetrics
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.monitoring import (
    provide_create_metric,
    provide_get_device_metrics,
)


def create_metric_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateMetric:
    return provide_create_metric(session)


def get_device_metrics_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDeviceMetrics:
    return provide_get_device_metrics(session)
