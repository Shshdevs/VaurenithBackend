from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1 import (
    DeviceGroup,
    DeviceGroupCreateRequest,
    DeviceGroupUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.device_group import (
    CreateDeviceGroup,
    DeleteDeviceGroup,
    GetDeviceGroup,
    UpdateDeviceGroup,
)


def build_device_group_router(
    create_device_group_dependency: Callable[..., CreateDeviceGroup],
    get_device_group_dependency: Callable[..., GetDeviceGroup],
    delete_device_group_dependency: Callable[..., DeleteDeviceGroup],
    update_device_group_dependency: Callable[..., UpdateDeviceGroup],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["device_groups"])

    @router.post(
        "/device-groups",
        response_model=ApiResponse[DeviceGroup],
        status_code=status.HTTP_201_CREATED,
    )
    async def create(
        request: DeviceGroupCreateRequest,
        create_device_group: CreateDeviceGroup = Depends(create_device_group_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DeviceGroup]:
        device_group = await create_device_group.execute(
            identity=identity, name=request.name, description=request.description
        )
        return ApiResponse[DeviceGroup](
            status=format_http_status(status.HTTP_201_CREATED),
            message="Device group is created successfully",
            data=DeviceGroup.model_validate(device_group),
        )

    @router.get(
        "/device-groups/{device_group_id}",
        response_model=ApiResponse[DeviceGroup],
        status_code=status.HTTP_200_OK,
    )
    async def get_device_group(
        device_group_id: UUID,
        get_device_group: GetDeviceGroup = Depends(get_device_group_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DeviceGroup]:
        device_group = await get_device_group.execute(
            identity=identity, device_group_id=device_group_id
        )
        return ApiResponse[DeviceGroup](
            status=format_http_status(status.HTTP_200_OK),
            data=DeviceGroup.model_validate(device_group),
        )

    @router.put(
        "/device-groups/{device_group_id}",
        response_model=ApiResponse[DeviceGroup],
        status_code=status.HTTP_200_OK,
    )
    async def update(
        device_group_id: UUID,
        request: DeviceGroupUpdateRequest,
        update_device_group: UpdateDeviceGroup = Depends(update_device_group_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DeviceGroup]:
        device_group = await update_device_group.execute(
            identity=identity,
            device_group_id=device_group_id,
            name=request.name,
            description=request.description,
        )

        return ApiResponse[DeviceGroup](
            status=format_http_status(status.HTTP_200_OK),
            message="Device group is updated successfully",
            data=DeviceGroup.model_validate(device_group),
        )

    @router.delete(
        "/device-groups/{device_group_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_device_group(
        device_group_id: UUID,
        delete_device_group: DeleteDeviceGroup = Depends(delete_device_group_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_device_group.execute(
            identity=identity, device_group_id=device_group_id
        )
        return ApiResponse[None](
            status=format_http_status(status.HTTP_200_OK),
        )

    return router
