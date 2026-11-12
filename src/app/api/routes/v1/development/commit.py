from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.development import CommitCreateRequest, CommitData
from app.application.development import CreateCommit, GetCommit, GetRepositoryCommits
from app.application.identity import VerifiedIdentity
from app.domain.common.enums import EntityType


def build_commit_router(
    create_commit_dependency: Callable[..., CreateCommit],
    get_commit_dependency: Callable[..., GetCommit],
    get_repository_commits_dependency: Callable[..., GetRepositoryCommits],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["commits"])

    @router.post(
        "/repositories/{repository_id}/commits",
        response_model=ApiResponse[CommitData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_commit(
        repository_id: UUID,
        request: CommitCreateRequest,
        use_case: CreateCommit = Depends(create_commit_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[CommitData]:
        commit = await use_case.create_commit(
            identity,
            repository_id,
            request.hash,
            author_name=request.author_name,
            author_email=request.author_email,
            committed_at=request.committed_at,
            changed_files=request.changed_files,
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            code=ResponseCode.CACHED,
            entity_type=EntityType.COMMIT,
            data=CommitData.model_validate(commit),
        )

    @router.get(
        "/repositories/{repository_id}/commits",
        response_model=ApiResponse[list[CommitData]],
    )
    async def get_repository_commits(
        repository_id: UUID,
        use_case: GetRepositoryCommits = Depends(get_repository_commits_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[CommitData]]:
        commits = await use_case.get_repository_commits(identity, repository_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[CommitData.model_validate(commit) for commit in commits],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.COMMIT,
        )

    @router.get("/commits/{commit_id}", response_model=ApiResponse[CommitData])
    async def get_commit(
        commit_id: UUID,
        use_case: GetCommit = Depends(get_commit_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[CommitData]:
        commit = await use_case.get_commit(identity, commit_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=CommitData.model_validate(commit),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.COMMIT,
        )

    return router
