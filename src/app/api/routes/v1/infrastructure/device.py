from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1.infrastructure import (
    Device,
    DeviceCreateRequest,
    DeviceUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.device import (
    CreateDevice,
    DeleteDevice,
    GetDevice,
    GetUserDevices,
    UpdateDevice,
)


def build_device_router(
    create_device_dependency: Callable[..., CreateDevice],
    get_device_dependency: Callable[..., GetDevice],
    get_user_devices_dependency: Callable[..., GetUserDevices],
    update_device_dependency: Callable[..., UpdateDevice],
    delete_device_dependency: Callable[..., DeleteDevice],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["devices"])

    @router.post(
        "/devices",
        response_model=ApiResponse[Device],
        status_code=status.HTTP_201_CREATED,
    )
    async def create(
        request: DeviceCreateRequest,
        create_device: CreateDevice = Depends(create_device_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[Device]:
        device = await create_device.execute(identity=identity, **request.model_dump())
        return ApiResponse[Device](
            status=format_http_status(status.HTTP_201_CREATED),
            message="Device is created successfully",
            data=Device.model_validate(device),
        )

    @router.get(
        "/devices",
        response_model=ApiResponse[list[Device]],
        status_code=status.HTTP_200_OK,
    )
    async def get_user_devices(
        get_user_devices: GetUserDevices = Depends(get_user_devices_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[Device]]:
        devices = await get_user_devices.execute(identity=identity)
        return ApiResponse[list[Device]](
            status=format_http_status(status.HTTP_200_OK),
            data=[Device.model_validate(device) for device in devices],
        )

    @router.get(
        "/devices/{device_id}",
        response_model=ApiResponse[Device],
        status_code=status.HTTP_200_OK,
    )
    async def get_device(
        device_id: UUID,
        get_device: GetDevice = Depends(get_device_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[Device]:
        device = await get_device.execute(identity=identity, device_id=device_id)
        return ApiResponse[Device](
            status=format_http_status(status.HTTP_200_OK),
            data=Device.model_validate(device),
        )

    @router.put(
        "/devices/{device_id}",
        response_model=ApiResponse[Device],
        status_code=status.HTTP_200_OK,
    )
    async def update(
        device_id: UUID,
        request: DeviceUpdateRequest,
        update_device: UpdateDevice = Depends(update_device_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[Device]:
        device = await update_device.execute(
            identity=identity,
            device_id=device_id,
            expected_version=request.version,
            **request.model_dump(exclude={"version"}),
        )
        return ApiResponse[Device](
            status=format_http_status(status.HTTP_200_OK),
            message="Device is updated successfully",
            data=Device.model_validate(device),
        )

    @router.delete(
        "/devices/{device_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_device(
        device_id: UUID,
        delete_device: DeleteDevice = Depends(delete_device_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_device.execute(identity=identity, device_id=device_id)
        return ApiResponse[None](status=format_http_status(status.HTTP_200_OK))

    return router
