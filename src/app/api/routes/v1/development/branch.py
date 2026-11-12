from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.development import (
    BranchCreateRequest,
    BranchData,
    BranchUpdateRequest,
)
from app.application.development import (
    CreateBranch,
    DeleteBranch,
    GetBranch,
    GetRepositoryBranches,
    UpdateBranch,
)
from app.application.identity import VerifiedIdentity
from app.domain.common.enums import EntityType


def build_branch_router(
    create_branch_dependency: Callable[..., CreateBranch],
    get_branch_dependency: Callable[..., GetBranch],
    get_repository_branches_dependency: Callable[..., GetRepositoryBranches],
    update_branch_dependency: Callable[..., UpdateBranch],
    delete_branch_dependency: Callable[..., DeleteBranch],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["branches"])

    @router.post(
        "/repositories/{repository_id}/branches",
        response_model=ApiResponse[BranchData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_branch(
        repository_id: UUID,
        request: BranchCreateRequest,
        use_case: CreateBranch = Depends(create_branch_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[BranchData]:
        branch = await use_case.create_branch(
            identity, repository_id, **request.model_dump()
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            code=ResponseCode.CREATED,
            entity_type=EntityType.BRANCH,
            data=BranchData.model_validate(branch),
        )

    @router.get(
        "/repositories/{repository_id}/branches",
        response_model=ApiResponse[list[BranchData]],
    )
    async def get_repository_branches(
        repository_id: UUID,
        use_case: GetRepositoryBranches = Depends(get_repository_branches_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[BranchData]]:
        branches = await use_case.get_repository_branches(identity, repository_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[BranchData.model_validate(branch) for branch in branches],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.BRANCH,
        )

    @router.get("/branches/{branch_id}", response_model=ApiResponse[BranchData])
    async def get_branch(
        branch_id: UUID,
        use_case: GetBranch = Depends(get_branch_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[BranchData]:
        branch = await use_case.get_branch(identity, branch_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=BranchData.model_validate(branch),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.BRANCH,
        )

    @router.put("/branches/{branch_id}", response_model=ApiResponse[BranchData])
    async def update_branch(
        branch_id: UUID,
        request: BranchUpdateRequest,
        use_case: UpdateBranch = Depends(update_branch_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[BranchData]:
        branch = await use_case.update_branch(identity, branch_id, **request.model_dump())
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=BranchData.model_validate(branch),
            code=ResponseCode.UPDATED,
            entity_type=EntityType.BRANCH,
        )

    @router.delete("/branches/{branch_id}", response_model=ApiResponse[None])
    async def delete_branch(
        branch_id: UUID,
        use_case: DeleteBranch = Depends(delete_branch_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await use_case.delete_branch(identity, branch_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.DELETED,
            entity_type=None,
        )

    return router
