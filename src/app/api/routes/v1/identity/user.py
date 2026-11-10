from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends, status

from app.api.schemas import ApiResponse, format_http_status
from app.api.schemas.v1 import UserCreateRequest, UserData
from app.application.identity import (
    CreateUser,
    GetCurrentUser,
    RevokeSession,
    VerifiedIdentity,
)


def build_user_router(
    get_current_user_dependency: Callable[..., GetCurrentUser],
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

    @router.post("/users/logout", response_model=ApiResponse[None])
    async def logout(
        revoke_session: RevokeSession = Depends(revoke_session_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await revoke_session.execute(identity)
        return ApiResponse[None](
            message="Logged out successfully",
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
            message="User retrieved successfully",
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
            message="User created successfully",
            status=format_http_status(status.HTTP_201_CREATED),
            data=UserData.model_validate(user),
        )

    return router
