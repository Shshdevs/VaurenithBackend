from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1.synchronization import (
    SyncStateCreateRequest,
    SyncStateData,
    SyncStateStatusUpdateRequest,
    SyncStateUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.synchronization.use_cases.sync_state import (
    CreateSyncState,
    DeleteSyncState,
    GetSyncState,
    UpdateSyncState,
    UpdateSyncStatus,
)


def build_sync_state_route(
    get_create_sync_state_dependency: Callable[..., CreateSyncState],
    get_get_sync_state_dependency: Callable[..., GetSyncState],
    get_delete_sync_state_dependency: Callable[..., DeleteSyncState],
    get_update_sync_state_dependency: Callable[..., UpdateSyncState],
    get_update_sync_status_dependency: Callable[..., UpdateSyncStatus],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["sync-state"])

    @router.post(
        "/sync-state",
        response_model=ApiResponse[SyncStateData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_sync_state(
        request: SyncStateCreateRequest,
        create_sync_state: CreateSyncState = Depends(get_create_sync_state_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[SyncStateData]:
        sync_state = await create_sync_state.execute(
            identity=identity,
            client_device_id=request.client_device_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            local_version=request.local_version,
            server_version=request.server_version,
            status=request.status,
        )
        return ApiResponse[SyncStateData](
            status=format_http_status(status.HTTP_201_CREATED),
            data=SyncStateData.model_validate(sync_state),
            message="Sync state is created successfully",
        )

    @router.put(
        "/sync-state/{sync_state_id}",
        response_model=ApiResponse[SyncStateData],
        status_code=status.HTTP_200_OK,
    )
    async def update_sync_state(
        sync_state_id: UUID,
        request: SyncStateUpdateRequest,
        update_sync_state: UpdateSyncState = Depends(get_update_sync_state_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[SyncStateData]:
        sync_state = await update_sync_state.execute(
            sync_state_id=sync_state_id,
            identity=identity,
            expected_version=request.expected_version,
            server_version=request.server_version,
            status=request.status,
            last_error=request.last_error,
        )
        return ApiResponse[SyncStateData](
            status=format_http_status(status.HTTP_200_OK),
            data=SyncStateData.model_validate(sync_state),
            message="Sync state is updated successfully",
        )

    @router.patch(
        "/sync-state/{sync_state_id}/status",
        response_model=ApiResponse[SyncStateData],
        status_code=status.HTTP_200_OK,
    )
    async def update_sync_status(
        sync_state_id: UUID,
        request: SyncStateStatusUpdateRequest,
        update_sync_status: UpdateSyncStatus = Depends(get_update_sync_status_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[SyncStateData]:
        sync_state = await update_sync_status.execute(
            sync_state_id=sync_state_id,
            identity=identity,
            status=request.status,
        )
        return ApiResponse[SyncStateData](
            status=format_http_status(status.HTTP_200_OK),
            data=SyncStateData.model_validate(sync_state),
            message="Sync state status is updated",
        )

    @router.get(
        "/sync-state/{sync_state_id}",
        response_model=ApiResponse[SyncStateData],
        status_code=status.HTTP_200_OK,
    )
    async def get_sync_state(
        sync_state_id: UUID,
        get_sync_state: GetSyncState = Depends(get_get_sync_state_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[SyncStateData]:
        sync_state = await get_sync_state.execute(
            identity=identity, sync_state_id=sync_state_id
        )
        return ApiResponse[SyncStateData](
            status=format_http_status(status.HTTP_200_OK),
            data=SyncStateData.model_validate(sync_state),
            message="Success",
        )

    @router.delete(
        "/sync-state/{sync_state_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_sync_state(
        sync_state_id: UUID,
        delete_sync_state: DeleteSyncState = Depends(get_delete_sync_state_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_sync_state.execute(
            sync_state_id=sync_state_id,
            identity=identity,
        )
        return ApiResponse[None](
            status=format_http_status(status.HTTP_200_OK),
            message="Sync state is deleted successfully",
        )

    return router
