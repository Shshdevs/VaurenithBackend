from collections.abc import Awaitable, Callable
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1.monitoring import (
    LogMetadataCreateRequest,
    LogMetadataData,
)
from app.application.identity import VerifiedIdentity
from app.application.monitoring import CreateLogMetadata, GetUserLogMetadata


def build_log_metadata_router(
    create_log_metadata_dependency: Callable[..., CreateLogMetadata],
    get_user_log_metadata_dependency: Callable[..., GetUserLogMetadata],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["monitoring"])

    @router.post(
        "/logs/metadata",
        response_model=ApiResponse[LogMetadataData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_log_metadata(
        request: LogMetadataCreateRequest,
        use_case: CreateLogMetadata = Depends(create_log_metadata_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[LogMetadataData]:
        value = await use_case.create_log_metadata(
            identity=identity,
            source=request.source,
            project_id=request.project_id,
            device_id=request.device_id,
            service_id=request.service_id,
            container_id=request.container_id,
            reference=request.reference,
            description=request.description,
            severity=request.severity,
            records_count=request.records_count,
            collected_at=request.collected_at,
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            message="Log metadata recorded successfully",
            data=LogMetadataData.model_validate(value),
        )

    @router.get(
        "/logs/metadata",
        response_model=ApiResponse[list[LogMetadataData]],
    )
    async def get_user_log_metadata(
        project_id: UUID | None = Query(default=None),
        device_id: UUID | None = Query(default=None),
        service_id: UUID | None = Query(default=None),
        container_id: UUID | None = Query(default=None),
        source: str | None = Query(default=None, max_length=255),
        severity: str | None = Query(default=None, max_length=50),
        start: datetime | None = Query(default=None),
        end: datetime | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        use_case: GetUserLogMetadata = Depends(get_user_log_metadata_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[LogMetadataData]]:
        values = await use_case.get_user_log_metadata(
            identity,
            project_id,
            device_id,
            service_id,
            container_id,
            source,
            severity,
            start,
            end,
            limit,
            offset,
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            message="Log metadata retrieved successfully",
            data=[LogMetadataData.model_validate(value) for value in values],
        )

    return router
