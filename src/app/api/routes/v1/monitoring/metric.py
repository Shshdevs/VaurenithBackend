from collections.abc import Awaitable, Callable
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.response import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.monitoring import MetricCreateRequest, MetricData
from app.application.identity import VerifiedIdentity
from app.application.monitoring import CreateMetric, GetDeviceMetrics
from app.domain.common.enums import EntityType


def build_metric_router(
    create_metric_dependency: Callable[..., CreateMetric],
    get_device_metrics_dependency: Callable[..., GetDeviceMetrics],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["metrics"])

    @router.post(
        "/devices/{device_id}/metrics",
        response_model=ApiResponse[MetricData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_metric(
        device_id: UUID,
        request: MetricCreateRequest,
        use_case: CreateMetric = Depends(create_metric_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[MetricData]:
        metric = await use_case.create_metric(
            identity=identity,
            device_id=device_id,
            metric_type=request.metric_type,
            value=request.value,
            unit=request.unit,
            collected_at=request.collected_at,
            source=request.source,
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            code=ResponseCode.RECORDED,
            entity_type=EntityType.METRIC,
            data=MetricData.model_validate(metric),
        )

    @router.get(
        "/devices/{device_id}/metrics",
        response_model=ApiResponse[list[MetricData]],
    )
    async def get_device_metrics(
        device_id: UUID,
        start: datetime | None = Query(default=None),
        end: datetime | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        use_case: GetDeviceMetrics = Depends(get_device_metrics_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[MetricData]]:
        metrics = await use_case.get_device_metrics(
            identity, device_id, start, end, limit, offset
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.METRIC,
            data=[MetricData.model_validate(metric) for metric in metrics],
        )

    return router
