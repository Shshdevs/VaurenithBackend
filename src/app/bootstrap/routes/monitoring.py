from fastapi import APIRouter

from app.api.routes.v1.monitoring.metric import build_metric_router
from app.bootstrap.dependencies.identity import get_authenticated_identity
from app.bootstrap.dependencies.monitoring import (
    create_metric_dependency,
    get_device_metrics_dependency,
)


def build_monitoring_api_router() -> APIRouter:
    return build_metric_router(
        create_metric_dependency=create_metric_dependency,
        get_device_metrics_dependency=get_device_metrics_dependency,
        authenticated_identity_dependency=get_authenticated_identity,
    )
