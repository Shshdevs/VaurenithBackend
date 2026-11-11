from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1.preferences.setting import (
    SettingCreateRequest,
    SettingData,
    SettingUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.preferences.use_cases.settings import (
    CreateSetting,
    DeleteSetting,
    GetSetting,
    GetSettings,
    UpdateSetting,
)
from app.domain.preferences import SettingScope


def build_settings_router(
    get_settings_dependency: Callable[..., GetSettings],
    get_setting_dependency: Callable[..., GetSetting],
    create_setting_dependency: Callable[..., CreateSetting],
    update_setting_dependency: Callable[..., UpdateSetting],
    delete_setting_dependency: Callable[..., DeleteSetting],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["settings"])

    @router.get("/settings", response_model=ApiResponse[list[SettingData]])
    async def list_settings(
        scope: SettingScope = Query(...),
        client_device_id: UUID | None = Query(default=None),
        use_case: GetSettings = Depends(get_settings_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[SettingData]]:
        items = await use_case.execute(identity, scope, client_device_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[SettingData.model_validate(item) for item in items],
        )

    @router.get("/settings/{setting_id}", response_model=ApiResponse[SettingData])
    async def get_setting(
        setting_id: UUID,
        use_case: GetSetting = Depends(get_setting_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[SettingData]:
        item = await use_case.execute(identity, setting_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=SettingData.model_validate(item),
        )

    @router.post(
        "/settings",
        response_model=ApiResponse[SettingData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_setting(
        request: SettingCreateRequest,
        use_case: CreateSetting = Depends(create_setting_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[SettingData]:
        item = await use_case.create_setting(
            identity, request.scope, request.key, request.value, request.client_device_id
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            message="Setting created successfully",
            data=SettingData.model_validate(item),
        )

    @router.put("/settings/{setting_id}", response_model=ApiResponse[SettingData])
    async def update_setting(
        setting_id: UUID,
        request: SettingUpdateRequest,
        use_case: UpdateSetting = Depends(update_setting_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[SettingData]:
        item = await use_case.update_setting(
            identity, setting_id, request.expected_version, request.value
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            message="Setting updated successfully",
            data=SettingData.model_validate(item),
        )

    @router.delete("/settings/{setting_id}", response_model=ApiResponse[None])
    async def delete_setting(
        setting_id: UUID,
        expected_version: int = Query(ge=1, le=2**63 - 2),
        use_case: DeleteSetting = Depends(delete_setting_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await use_case.execute(identity, setting_id, expected_version)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            message="Setting deleted successfully",
        )

    return router
