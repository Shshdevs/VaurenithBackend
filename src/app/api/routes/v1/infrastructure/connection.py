from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1 import (
    ConnectionCreateRequest,
    ConnectionData,
    ConnectionStatusUpdateRequest,
    ConnectionUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.connection import (
    CreateConnection,
    DeleteConnection,
    GetConnection,
    GetDeviceConnections,
    GetUserConnections,
    ReportConnectionStatus,
    UpdateConnection,
)


def build_connection_router(
    create_connection_dependency: Callable[..., CreateConnection],
    get_connection_dependency: Callable[..., GetConnection],
    get_user_connections_dependency: Callable[..., GetUserConnections],
    get_device_connections_dependency: Callable[..., GetDeviceConnections],
    update_connection_dependency: Callable[..., UpdateConnection],
    report_connection_status_dependency: Callable[..., ReportConnectionStatus],
    delete_connection_dependency: Callable[..., DeleteConnection],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["connections"])

    @router.post(
        "/connections",
        response_model=ApiResponse[ConnectionData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create(
        request: ConnectionCreateRequest,
        create_connection: CreateConnection = Depends(create_connection_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ConnectionData]:
        connection = await create_connection.execute(
            identity=identity, **request.model_dump()
        )
        return ApiResponse[ConnectionData](
            status=format_http_status(status.HTTP_201_CREATED),
            message="Connection is created successfully",
            data=ConnectionData.model_validate(connection),
        )

    @router.get(
        "/connections",
        response_model=ApiResponse[list[ConnectionData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_user_connections(
        get_user_connections: GetUserConnections = Depends(get_user_connections_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ConnectionData]]:
        connections = await get_user_connections.execute(identity)
        return ApiResponse[list[ConnectionData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ConnectionData.model_validate(connection) for connection in connections],
        )

    @router.get(
        "/connections/{connection_id}",
        response_model=ApiResponse[ConnectionData],
        status_code=status.HTTP_200_OK,
    )
    async def get_connection(
        connection_id: UUID,
        get_connection: GetConnection = Depends(get_connection_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ConnectionData]:
        connection = await get_connection.execute(identity, connection_id)
        return ApiResponse[ConnectionData](
            status=format_http_status(status.HTTP_200_OK),
            data=ConnectionData.model_validate(connection),
        )

    @router.get(
        "/devices/{device_id}/connections",
        response_model=ApiResponse[list[ConnectionData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_device_connections(
        device_id: UUID,
        get_device_connections: GetDeviceConnections = Depends(
            get_device_connections_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ConnectionData]]:
        connections = await get_device_connections.execute(identity, device_id)
        return ApiResponse[list[ConnectionData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ConnectionData.model_validate(connection) for connection in connections],
        )

    @router.put(
        "/connections/{connection_id}",
        response_model=ApiResponse[ConnectionData],
        status_code=status.HTTP_200_OK,
    )
    async def update(
        connection_id: UUID,
        request: ConnectionUpdateRequest,
        update_connection: UpdateConnection = Depends(update_connection_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ConnectionData]:
        connection = await update_connection.execute(
            identity=identity,
            connection_id=connection_id,
            expected_version=request.version,
            **request.model_dump(exclude={"version"}),
        )
        return ApiResponse[ConnectionData](
            status=format_http_status(status.HTTP_200_OK),
            message="Connection is updated successfully",
            data=ConnectionData.model_validate(connection),
        )

    @router.patch(
        "/connections/{connection_id}/status",
        response_model=ApiResponse[ConnectionData],
        status_code=status.HTTP_200_OK,
    )
    async def report_status(
        connection_id: UUID,
        request: ConnectionStatusUpdateRequest,
        report_connection_status: ReportConnectionStatus = Depends(
            report_connection_status_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ConnectionData]:
        connection = await report_connection_status.execute(
            identity=identity,
            connection_id=connection_id,
            expected_version=request.version,
            status=request.status,
            last_connected_at=request.last_connected_at,
            last_error=request.last_error,
        )
        return ApiResponse[ConnectionData](
            status=format_http_status(status.HTTP_200_OK),
            message="Connection status is updated successfully",
            data=ConnectionData.model_validate(connection),
        )

    @router.delete(
        "/connections/{connection_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_connection(
        connection_id: UUID,
        delete_connection: DeleteConnection = Depends(delete_connection_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_connection.execute(identity, connection_id)
        return ApiResponse[None](status=format_http_status(status.HTTP_200_OK))

    return router
