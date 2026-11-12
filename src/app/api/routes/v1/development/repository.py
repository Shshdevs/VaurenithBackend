from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1.development import (
    RepositoryCreateRequest,
    RepositoryData,
    RepositoryUpdateRequest,
)
from app.application.development import (
    CreateRepository,
    DeleteRepository,
    GetProjectRepositories,
    GetRepository,
    GetUserRepositories,
    UpdateRepository,
)
from app.application.identity import VerifiedIdentity


def build_repository_router(
    create_repository_dependency: Callable[..., CreateRepository],
    get_repository_dependency: Callable[..., GetRepository],
    get_user_repositories_dependency: Callable[..., GetUserRepositories],
    get_project_repositories_dependency: Callable[..., GetProjectRepositories],
    update_repository_dependency: Callable[..., UpdateRepository],
    delete_repository_dependency: Callable[..., DeleteRepository],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["repositories"])

    @router.post(
        "/projects/{project_id}/repositories",
        response_model=ApiResponse[RepositoryData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_repository(
        project_id: UUID,
        request: RepositoryCreateRequest,
        use_case: CreateRepository = Depends(create_repository_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[RepositoryData]:
        repository = await use_case.create_repository(
            identity=identity,
            project_id=project_id,
            name=request.name,
            description=request.description,
            remote_url=request.remote_url,
            default_branch=request.default_branch,
            repository_type=request.repository_type,
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            message="Repository created successfully",
            data=RepositoryData.model_validate(repository),
        )

    @router.get("/repositories", response_model=ApiResponse[list[RepositoryData]])
    async def get_user_repositories(
        use_case: GetUserRepositories = Depends(get_user_repositories_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[RepositoryData]]:
        repositories = await use_case.get_user_repositories(identity)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[RepositoryData.model_validate(repository) for repository in repositories],
        )

    @router.get(
        "/projects/{project_id}/repositories",
        response_model=ApiResponse[list[RepositoryData]],
    )
    async def get_project_repositories(
        project_id: UUID,
        use_case: GetProjectRepositories = Depends(get_project_repositories_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[RepositoryData]]:
        repositories = await use_case.get_project_repositories(identity, project_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[RepositoryData.model_validate(repository) for repository in repositories],
        )

    @router.get("/repositories/{repository_id}", response_model=ApiResponse[RepositoryData])
    async def get_repository(
        repository_id: UUID,
        use_case: GetRepository = Depends(get_repository_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[RepositoryData]:
        repository = await use_case.get_repository(identity, repository_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=RepositoryData.model_validate(repository),
        )

    @router.put("/repositories/{repository_id}", response_model=ApiResponse[RepositoryData])
    async def update_repository(
        repository_id: UUID,
        request: RepositoryUpdateRequest,
        use_case: UpdateRepository = Depends(update_repository_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[RepositoryData]:
        repository = await use_case.update_repository(
            identity=identity,
            repository_id=repository_id,
            expected_version=request.version,
            name=request.name,
            description=request.description,
            remote_url=request.remote_url,
            default_branch=request.default_branch,
            repository_type=request.repository_type,
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            message="Repository updated successfully",
            data=RepositoryData.model_validate(repository),
        )

    @router.delete("/repositories/{repository_id}", response_model=ApiResponse[None])
    async def delete_repository(
        repository_id: UUID,
        expected_version: int = Query(ge=1, le=2**63 - 2),
        use_case: DeleteRepository = Depends(delete_repository_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await use_case.delete_repository(identity, repository_id, expected_version)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            message="Repository deleted successfully",
        )

    return router
