from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.projects import (
    ProjectCreateRequest,
    ProjectData,
    ProjectUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.projects.use_cases.projects import (
    CreateProject,
    DeleteProject,
    GetProject,
    GetUserProjects,
    UpdateProject,
)
from app.domain.common.enums import EntityType


def build_project_route(
    create_project_dependency: Callable[..., CreateProject],
    get_project_dependency: Callable[..., GetProject],
    get_user_projects_dependency: Callable[..., GetUserProjects],
    update_project_dependency: Callable[..., UpdateProject],
    delete_project_dependency: Callable[..., DeleteProject],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["projects"])

    @router.post(
        "/projects",
        response_model=ApiResponse[ProjectData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create(
        request: ProjectCreateRequest,
        create_project: CreateProject = Depends(create_project_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ProjectData]:
        project = await create_project.execute(
            identity=identity,
            name=request.name,
            project_type=request.project_type,
            version=request.version,
            description=request.description,
            metadata=request.metadata,
        )
        return ApiResponse[ProjectData](
            status=format_http_status(status.HTTP_201_CREATED),
            code=ResponseCode.CREATED,
            entity_type=EntityType.PROJECT,
            data=ProjectData.model_validate(project),
        )

    @router.get(
        "/projects/{project_id}",
        response_model=ApiResponse[ProjectData],
        status_code=status.HTTP_200_OK,
    )
    async def get_project(
        project_id: UUID,
        get_project: GetProject = Depends(get_project_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ProjectData]:
        project = await get_project.execute(identity=identity, project_id=project_id)
        return ApiResponse[ProjectData](
            status=format_http_status(status.HTTP_200_OK),
            data=ProjectData.model_validate(project),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.PROJECT,
        )

    @router.get(
        "/projects",
        response_model=ApiResponse[list[ProjectData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_user_projects(
        get_user_projects: GetUserProjects = Depends(get_user_projects_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ProjectData]]:
        projects = await get_user_projects.execute(identity=identity)
        return ApiResponse[list[ProjectData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ProjectData.model_validate(project) for project in projects],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.PROJECT,
        )

    @router.put(
        "/projects/{project_id}",
        response_model=ApiResponse[ProjectData],
        status_code=status.HTTP_200_OK,
    )
    async def update_project(
        project_id: UUID,
        request: ProjectUpdateRequest,
        update_project: UpdateProject = Depends(update_project_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ProjectData]:
        result = await update_project.execute(
            identity=identity,
            project_id=project_id,
            name=request.name,
            description=request.description,
            project_type=request.project_type,
            status=request.status,
            expected_version=request.version,
            metadata=request.metadata,
        )

        return ApiResponse[ProjectData](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.UPDATED,
            entity_type=EntityType.PROJECT,
            data=ProjectData.model_validate(result),
        )

    @router.delete(
        "/projects/{project_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_project(
        project_id: UUID,
        delete_project: DeleteProject = Depends(delete_project_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_project.execute(
            identity=identity,
            project_id=project_id,
        )
        return ApiResponse[None](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.DELETED,
            entity_type=EntityType.PROJECT,
        )

    return router
