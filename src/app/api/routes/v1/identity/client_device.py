from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.identity import (
    ClientDeviceData as ClientDeviceSchema,
)
from app.api.schemas.v1.identity import (
    ClientDeviceRegisterRequest,
    ClientDeviceStatusRequest,
    ClientDeviceUpdateRequest,
)
from app.api.schemas.v1.identity import (
    SessionData as SessionSchema,
)
from app.application.identity import (
    CreateDeviceSession,
    GetClientDevice,
    ListClientDevices,
    ListDeviceSessions,
    RegisterClientDevice,
    RevokeClientDevice,
    SetClientDeviceStatus,
    UpdateClientDevice,
    VerifiedIdentity,
)
from app.domain.common.enums import EntityType
from app.domain.identity import ClientDeviceStatus


def build_client_device_router(
    register_client_device_dependency: Callable[..., RegisterClientDevice],
    list_client_devices_dependency: Callable[..., ListClientDevices],
    get_client_device_dependency: Callable[..., GetClientDevice],
    update_client_device_dependency: Callable[..., UpdateClientDevice],
    create_device_session_dependency: Callable[..., CreateDeviceSession],
    list_device_sessions_dependency: Callable[..., ListDeviceSessions],
    set_client_device_status_dependency: Callable[..., SetClientDeviceStatus],
    revoke_client_device_dependency: Callable[..., RevokeClientDevice],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
    verified_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["client devices"])

    @router.post(
        "/users/me/devices",
        response_model=ApiResponse[ClientDeviceSchema],
        status_code=status.HTTP_201_CREATED,
    )
    async def register_device(
        request: ClientDeviceRegisterRequest,
        use_case: RegisterClientDevice = Depends(register_client_device_dependency),
        identity: VerifiedIdentity = Depends(verified_identity_dependency),
    ) -> ApiResponse[ClientDeviceSchema]:
        device = await use_case.execute(identity, **request.model_dump())
        return ApiResponse[ClientDeviceSchema](
            code=ResponseCode.CREATED,
            entity_type=EntityType.CLIENT_DEVICE,
            status=format_http_status(status.HTTP_201_CREATED),
            data=ClientDeviceSchema.model_validate(device),
        )

    @router.get(
        "/users/me/devices",
        response_model=ApiResponse[list[ClientDeviceSchema]],
    )
    async def list_devices(
        use_case: ListClientDevices = Depends(list_client_devices_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ClientDeviceSchema]]:
        devices = await use_case.execute(identity)
        return ApiResponse[list[ClientDeviceSchema]](
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.CLIENT_DEVICE,
            status=format_http_status(status.HTTP_200_OK),
            data=[ClientDeviceSchema.model_validate(device) for device in devices],
        )

    @router.get(
        "/users/me/devices/{device_id}",
        response_model=ApiResponse[ClientDeviceSchema],
    )
    async def get_device(
        device_id: UUID,
        use_case: GetClientDevice = Depends(get_client_device_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ClientDeviceSchema]:
        device = await use_case.execute(identity, device_id)
        return ApiResponse[ClientDeviceSchema](
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.CLIENT_DEVICE,
            status=format_http_status(status.HTTP_200_OK),
            data=ClientDeviceSchema.model_validate(device),
        )

    @router.patch(
        "/users/me/devices/{device_id}",
        response_model=ApiResponse[ClientDeviceSchema],
    )
    async def update_device(
        device_id: UUID,
        request: ClientDeviceUpdateRequest,
        use_case: UpdateClientDevice = Depends(update_client_device_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ClientDeviceSchema]:
        device = await use_case.execute(
            identity=identity,
            device_id=device_id,
            name=request.name,
            app_version=request.app_version,
            app_version_provided="app_version" in request.model_fields_set,
        )
        return ApiResponse[ClientDeviceSchema](
            code=ResponseCode.UPDATED,
            entity_type=EntityType.CLIENT_DEVICE,
            status=format_http_status(status.HTTP_200_OK),
            data=ClientDeviceSchema.model_validate(device),
        )

    @router.post(
        "/users/me/devices/{device_id}/sessions",
        response_model=ApiResponse[SessionSchema],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_device_session(
        device_id: UUID,
        use_case: CreateDeviceSession = Depends(create_device_session_dependency),
        identity: VerifiedIdentity = Depends(verified_identity_dependency),
    ) -> ApiResponse[SessionSchema]:
        session = await use_case.execute(identity, device_id)
        return ApiResponse[SessionSchema](
            code=ResponseCode.CREATED,
            entity_type=EntityType.SESSION,
            status=format_http_status(status.HTTP_201_CREATED),
            data=SessionSchema.model_validate(session),
        )

    @router.get(
        "/users/me/devices/{device_id}/sessions",
        response_model=ApiResponse[list[SessionSchema]],
    )
    async def list_device_sessions(
        device_id: UUID,
        use_case: ListDeviceSessions = Depends(list_device_sessions_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[SessionSchema]]:
        sessions = await use_case.execute(identity, device_id)
        return ApiResponse[list[SessionSchema]](
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.SESSION,
            status=format_http_status(status.HTTP_200_OK),
            data=[SessionSchema.model_validate(session) for session in sessions],
        )

    @router.patch(
        "/users/me/devices/{device_id}/status",
        response_model=ApiResponse[ClientDeviceSchema],
    )
    async def set_device_status(
        device_id: UUID,
        request: ClientDeviceStatusRequest,
        use_case: SetClientDeviceStatus = Depends(set_client_device_status_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ClientDeviceSchema]:
        device = await use_case.execute(
            identity, device_id, ClientDeviceStatus(request.status)
        )
        return ApiResponse[ClientDeviceSchema](
            code=ResponseCode.STATUS_UPDATED,
            entity_type=EntityType.CLIENT_DEVICE,
            status=format_http_status(status.HTTP_200_OK),
            data=ClientDeviceSchema.model_validate(device),
        )

    @router.delete("/users/me/devices/{device_id}", response_model=ApiResponse[None])
    async def revoke_device(
        device_id: UUID,
        use_case: RevokeClientDevice = Depends(revoke_client_device_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await use_case.execute(identity, device_id)
        return ApiResponse[None](
            code=ResponseCode.DELETED,
            entity_type=EntityType.CLIENT_DEVICE,
            status=format_http_status(status.HTTP_200_OK),
            data=None,
        )

    return router
