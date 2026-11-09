from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1 import (
    EnvironmentCreateRequest,
    EnvironmentData,
    EnvironmentUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import EnvironmentNotFound
from app.application.projects.use_cases.environments import (
    CreateEnvironment,
    DeleteEnvironment,
    GetEnvironment,
    GetProjectEnvironments,
    UpdateEnvironment,
)
from app.application.projects.use_cases.projects import GetProject


def build_environment_route(
    create_environment_dependency: Callable[..., CreateEnvironment],
    get_environment_dependency: Callable[..., GetEnvironment],
    get_project_environments_dependency: Callable[..., GetProjectEnvironments],
    update_environment_dependency: Callable[..., UpdateEnvironment],
    delete_environment_dependency: Callable[..., DeleteEnvironment],
    get_project_dependency: Callable[..., GetProject],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["environments"])

    @router.post(
        "/projects/{project_id}/environments",
        response_model=ApiResponse[EnvironmentData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_environment(
        project_id: UUID,
        request: EnvironmentCreateRequest,
        create_environment: CreateEnvironment = Depends(create_environment_dependency),
        get_project: GetProject = Depends(get_project_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[EnvironmentData]:
        await get_project.execute(identity=identity, project_id=project_id)
        environment = await create_environment.execute(
            identity=identity,
            project_id=project_id,
            name=request.name,
            environment_type=request.environment_type,
            description=request.description,
            configuration=request.configuration,
            version=request.version,
        )
        return ApiResponse[EnvironmentData](
            status=format_http_status(status.HTTP_201_CREATED),
            message="Environment created successfully",
            data=EnvironmentData.model_validate(environment),
        )

    @router.get(
        "/projects/{project_id}/environments",
        response_model=ApiResponse[list[EnvironmentData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_project_environments(
        project_id: UUID,
        get_project_environments: GetProjectEnvironments = Depends(
            get_project_environments_dependency
        ),
        get_project: GetProject = Depends(get_project_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[EnvironmentData]]:
        await get_project.execute(identity=identity, project_id=project_id)
        environments = await get_project_environments.execute(
            identity=identity, project_id=project_id
        )
        return ApiResponse[list[EnvironmentData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[EnvironmentData.model_validate(item) for item in environments],
        )

    @router.get(
        "/projects/{project_id}/environments/{environment_id}",
        response_model=ApiResponse[EnvironmentData],
        status_code=status.HTTP_200_OK,
    )
    async def get_environment(
        project_id: UUID,
        environment_id: UUID,
        get_environment: GetEnvironment = Depends(get_environment_dependency),
        get_project: GetProject = Depends(get_project_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[EnvironmentData]:
        await get_project.execute(identity=identity, project_id=project_id)
        environment = await get_environment.execute(identity, environment_id)
        if environment.project_id != project_id:
            raise EnvironmentNotFound(str(environment_id))
        return ApiResponse[EnvironmentData](
            status=format_http_status(status.HTTP_200_OK),
            data=EnvironmentData.model_validate(environment),
        )

    @router.put(
        "/projects/{project_id}/environments/{environment_id}",
        response_model=ApiResponse[EnvironmentData],
        status_code=status.HTTP_200_OK,
    )
    async def update_environment(
        project_id: UUID,
        environment_id: UUID,
        request: EnvironmentUpdateRequest,
        update_environment: UpdateEnvironment = Depends(update_environment_dependency),
        get_environment: GetEnvironment = Depends(get_environment_dependency),
        get_project: GetProject = Depends(get_project_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[EnvironmentData]:
        await get_project.execute(identity=identity, project_id=project_id)
        current_environment = await get_environment.execute(identity, environment_id)
        if current_environment.project_id != project_id:
            raise EnvironmentNotFound(str(environment_id))
        environment = await update_environment.execute(
            identity=identity,
            environment_id=environment_id,
            project_id=project_id,
            name=request.name,
            environment_type=request.environment_type,
            description=request.description,
            configuration=request.configuration,
            expected_version=request.version,
        )
        return ApiResponse[EnvironmentData](
            status=format_http_status(status.HTTP_200_OK),
            message="Environment updated successfully",
            data=EnvironmentData.model_validate(environment),
        )

    @router.delete(
        "/projects/{project_id}/environments/{environment_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_environment(
        project_id: UUID,
        environment_id: UUID,
        delete_environment: DeleteEnvironment = Depends(delete_environment_dependency),
        get_environment: GetEnvironment = Depends(get_environment_dependency),
        get_project: GetProject = Depends(get_project_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await get_project.execute(identity=identity, project_id=project_id)
        environment = await get_environment.execute(identity, environment_id)
        if environment.project_id != project_id:
            raise EnvironmentNotFound(str(environment_id))
        await delete_environment.execute(identity, environment_id)
        return ApiResponse[None](
            status=format_http_status(status.HTTP_200_OK),
            message="Environment deleted successfully",
        )

    return router
