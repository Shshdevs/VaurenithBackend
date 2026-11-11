from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1.development import (
    CodeComponentCreateRequest,
    CodeComponentData,
    CodeComponentUpdateRequest,
)
from app.application.development import (
    CreateCodeComponent,
    DeleteCodeComponent,
    GetCodeComponent,
    GetRepositoryCodeComponents,
    UpdateCodeComponent,
)
from app.application.identity import VerifiedIdentity


def build_code_component_router(
    create_code_component_dependency: Callable[..., CreateCodeComponent],
    get_code_component_dependency: Callable[..., GetCodeComponent],
    get_repository_code_components_dependency: Callable[..., GetRepositoryCodeComponents],
    update_code_component_dependency: Callable[..., UpdateCodeComponent],
    delete_code_component_dependency: Callable[..., DeleteCodeComponent],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["development"])

    @router.post(
        "/repositories/{repository_id}/code-components",
        response_model=ApiResponse[CodeComponentData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_code_component(
        repository_id: UUID,
        request: CodeComponentCreateRequest,
        use_case: CreateCodeComponent = Depends(create_code_component_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[CodeComponentData]:
        component = await use_case.create_code_component(
            identity, repository_id, **request.model_dump()
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            message="Code component created successfully",
            data=CodeComponentData.model_validate(component),
        )

    @router.get(
        "/repositories/{repository_id}/code-components",
        response_model=ApiResponse[list[CodeComponentData]],
    )
    async def get_repository_code_components(
        repository_id: UUID,
        use_case: GetRepositoryCodeComponents = Depends(
            get_repository_code_components_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[CodeComponentData]]:
        components = await use_case.get_repository_code_components(identity, repository_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[CodeComponentData.model_validate(component) for component in components],
        )

    @router.get(
        "/code-components/{component_id}",
        response_model=ApiResponse[CodeComponentData],
    )
    async def get_code_component(
        component_id: UUID,
        use_case: GetCodeComponent = Depends(get_code_component_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[CodeComponentData]:
        component = await use_case.get_code_component(identity, component_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=CodeComponentData.model_validate(component),
        )

    @router.put(
        "/code-components/{component_id}",
        response_model=ApiResponse[CodeComponentData],
    )
    async def update_code_component(
        component_id: UUID,
        request: CodeComponentUpdateRequest,
        use_case: UpdateCodeComponent = Depends(update_code_component_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[CodeComponentData]:
        values = request.model_dump()
        version = values.pop("version")
        component = await use_case.update_code_component(
            identity, component_id, version, **values
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=CodeComponentData.model_validate(component),
        )

    @router.delete("/code-components/{component_id}", response_model=ApiResponse[None])
    async def delete_code_component(
        component_id: UUID,
        expected_version: int = Query(ge=1, le=2**63 - 2),
        use_case: DeleteCodeComponent = Depends(delete_code_component_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await use_case.delete_code_component(identity, component_id, expected_version)
        return ApiResponse(status=format_http_status(status.HTTP_200_OK))

    return router
