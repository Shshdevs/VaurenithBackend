from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1 import ChangeLogData
from app.application.identity import VerifiedIdentity
from app.application.synchronization.change_log import GetUserChangeLog


def build_change_log_route(
    get_user_change_log_dependency: Callable[..., GetUserChangeLog],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["change-log"])

    @router.get(
        "/change-logs",
        response_model=ApiResponse[list[ChangeLogData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_change_log(
        after_sequence: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        use_case: GetUserChangeLog = Depends(get_user_change_log_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ChangeLogData]]:
        changes = await use_case.execute(identity, after_sequence, limit)
        return ApiResponse[list[ChangeLogData]](
            status=format_http_status(status.HTTP_200_OK),
            message="Change log retrieved successfully",
            data=[ChangeLogData.model_validate(change) for change in changes],
        )

    return router
