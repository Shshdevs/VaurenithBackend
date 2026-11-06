from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends, status

from ....application.identity.dto import VerifiedIdentity
from ....application.identity.use_cases import CreateUser, GetCurrentUser
from ...schemas import ApiResponse, format_http_status
from ...schemas.v1.user import UserData
from ...schemas.v1.user_create import UserCreateRequest


def build_user_router(
    get_current_user_dependency: Callable[..., GetCurrentUser],
    create_user_dependency: Callable[..., CreateUser],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
    verified_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["users"])

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
