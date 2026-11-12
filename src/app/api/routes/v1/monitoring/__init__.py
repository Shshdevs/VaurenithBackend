from collections.abc import Sequence

from fastapi import APIRouter

from app.api.routes.v1.monitoring.event import build_event_router
from app.api.routes.v1.monitoring.log_metadata import build_log_metadata_router
from app.api.routes.v1.monitoring.metric import build_metric_router


def build_monitoring_entity_router(entity_routers: Sequence[APIRouter]) -> APIRouter:
    router = APIRouter()
    for entity_router in entity_routers:
        router.include_router(entity_router)
    return router


__all__ = [
    "build_event_router",
    "build_log_metadata_router",
    "build_metric_router",
    "build_monitoring_entity_router",
]
