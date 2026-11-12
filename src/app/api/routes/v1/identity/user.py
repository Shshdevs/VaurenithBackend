from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends, status

from app.api.schemas import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.identity import UserCreateRequest, UserData
from app.application.identity import (
    CreateUser,
    DeleteUser,
    GetCurrentUser,
    RevokeSession,
    VerifiedIdentity,
)
from app.domain.common.enums import EntityType


def build_user_router(
    get_current_user_dependency: Callable[..., GetCurrentUser],
    delete_user_dependency: Callable[..., DeleteUser],
    create_user_dependency: Callable[..., CreateUser],
    revoke_session_dependency: Callable[..., RevokeSession],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
    verified_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["users"])

    @router.delete("/users/me", response_model=ApiResponse[None])
    async def delete_me(
        delete_user: DeleteUser = Depends(delete_user_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_user.execute(identity.user_id)
        return ApiResponse[None](
            code=ResponseCode.DELETED,
            entity_type=EntityType.USER,
            status=format_http_status(status.HTTP_200_OK),
            data=None,
        )

    @router.post("/users/logout", response_model=ApiResponse[None])
    async def logout(
        revoke_session: RevokeSession = Depends(revoke_session_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await revoke_session.execute(identity)
        return ApiResponse[None](
            code=ResponseCode.LOGGED_OUT,
            entity_type=EntityType.USER,
            status=format_http_status(status.HTTP_200_OK),
            data=None,
        )

    @router.get("/users/me", response_model=ApiResponse[UserData])
    async def get_me(
        get_current_user: GetCurrentUser = Depends(get_current_user_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[UserData]:
        user = await get_current_user.execute(identity.user_id)
        return ApiResponse[UserData](
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.USER,
            status=format_http_status(status.HTTP_200_OK),
            data=UserData.model_validate(user),
        )

    @router.post(
        "/users/create",
        response_model=ApiResponse[UserData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create(
        request: UserCreateRequest,
        create_user: CreateUser = Depends(create_user_dependency),
        identity: VerifiedIdentity = Depends(verified_identity_dependency),
    ) -> ApiResponse[UserData]:
        user = await create_user.execute(
            identity=identity,
            email=request.email,
            display_name=request.display_name,
            device_name=request.device_name,
            platform=request.platform,
            app_version=request.app_version,
        )
        return ApiResponse[UserData](
            code=ResponseCode.CREATED,
            entity_type=EntityType.USER,
            status=format_http_status(status.HTTP_201_CREATED),
            data=UserData.model_validate(user),
        )

    return router
