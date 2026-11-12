from collections.abc import Awaitable, Callable
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1.monitoring import EventCreateRequest, EventData
from app.application.identity import VerifiedIdentity
from app.application.monitoring import CreateEvent, GetUserEvents
from app.domain.monitoring import EventResult, EventType


def build_event_router(
    create_event_dependency: Callable[..., CreateEvent],
    get_user_events_dependency: Callable[..., GetUserEvents],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["events"])

    @router.post(
        "/events",
        response_model=ApiResponse[EventData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_event(
        request: EventCreateRequest,
        use_case: CreateEvent = Depends(create_event_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[EventData]:
        event = await use_case.create_event(
            identity=identity,
            event_type=request.event_type,
            result=request.result,
            created_at=request.created_at,
            project_id=request.project_id,
            device_id=request.device_id,
            description=request.description,
            metadata=request.metadata,
            client_device_id=request.client_device_id,
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            message="Event recorded successfully",
            data=EventData.model_validate(event),
        )

    @router.get("/events", response_model=ApiResponse[list[EventData]])
    async def get_user_events(
        project_id: UUID | None = Query(default=None),
        device_id: UUID | None = Query(default=None),
        event_type: EventType | None = Query(default=None),
        result: EventResult | None = Query(default=None),
        start: datetime | None = Query(default=None),
        end: datetime | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        use_case: GetUserEvents = Depends(get_user_events_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[EventData]]:
        events = await use_case.get_user_events(
            identity,
            project_id,
            device_id,
            event_type,
            result,
            start,
            end,
            limit,
            offset,
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            message="Events retrieved successfully",
            data=[EventData.model_validate(event) for event in events],
        )

    return router
