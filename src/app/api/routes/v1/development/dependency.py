from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1.development import (
    DependencyCreateRequest,
    DependencyData,
    DependencyUpdateRequest,
)
from app.application.development import (
    CreateDependency,
    DeleteDependency,
    GetComponentDependencies,
    GetDependency,
    GetRepositoryDependencies,
    UpdateDependency,
)
from app.application.identity import VerifiedIdentity


def build_dependency_router(
    create_dependency_dependency: Callable[..., CreateDependency],
    get_dependency_dependency: Callable[..., GetDependency],
    get_component_dependencies_dependency: Callable[..., GetComponentDependencies],
    get_repository_dependencies_dependency: Callable[..., GetRepositoryDependencies],
    update_dependency_dependency: Callable[..., UpdateDependency],
    delete_dependency_dependency: Callable[..., DeleteDependency],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["dependencies"])

    @router.post(
        "/repositories/{repository_id}/dependencies",
        response_model=ApiResponse[DependencyData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_dependency(
        repository_id: UUID,
        request: DependencyCreateRequest,
        use_case: CreateDependency = Depends(create_dependency_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DependencyData]:
        dependency = await use_case.create_dependency(
            identity, repository_id, **request.model_dump()
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            message="Dependency created successfully",
            data=DependencyData.model_validate(dependency),
        )

    @router.get(
        "/repositories/{repository_id}/dependencies",
        response_model=ApiResponse[list[DependencyData]],
    )
    async def get_repository_dependencies(
        repository_id: UUID,
        use_case: GetRepositoryDependencies = Depends(
            get_repository_dependencies_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[DependencyData]]:
        dependencies = await use_case.get_repository_dependencies(identity, repository_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[DependencyData.model_validate(item) for item in dependencies],
        )

    @router.get(
        "/code-components/{component_id}/dependencies",
        response_model=ApiResponse[list[DependencyData]],
    )
    async def get_component_dependencies(
        component_id: UUID,
        use_case: GetComponentDependencies = Depends(get_component_dependencies_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[DependencyData]]:
        dependencies = await use_case.get_component_dependencies(identity, component_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[DependencyData.model_validate(item) for item in dependencies],
        )

    @router.get("/dependencies/{dependency_id}", response_model=ApiResponse[DependencyData])
    async def get_dependency(
        dependency_id: UUID,
        use_case: GetDependency = Depends(get_dependency_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DependencyData]:
        dependency = await use_case.get_dependency(identity, dependency_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=DependencyData.model_validate(dependency),
        )

    @router.put("/dependencies/{dependency_id}", response_model=ApiResponse[DependencyData])
    async def update_dependency(
        dependency_id: UUID,
        request: DependencyUpdateRequest,
        use_case: UpdateDependency = Depends(update_dependency_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DependencyData]:
        dependency = await use_case.update_dependency(
            identity, dependency_id, **request.model_dump()
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=DependencyData.model_validate(dependency),
        )

    @router.delete("/dependencies/{dependency_id}", response_model=ApiResponse[None])
    async def delete_dependency(
        dependency_id: UUID,
        use_case: DeleteDependency = Depends(delete_dependency_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await use_case.delete_dependency(identity, dependency_id)
        return ApiResponse(status=format_http_status(status.HTTP_200_OK))

    return router
