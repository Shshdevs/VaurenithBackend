from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1 import ProjectCreateRequest, ProjectData
from app.application.identity import VerifiedIdentity
from app.application.projects import CreateProject


def build_project_route(
    create_project_dependency: Callable[..., CreateProject],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["projects"])

    @router.post(
        "/projects/create",
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
            message="Project created successfully",
            data=ProjectData.model_validate(project),
        )

    return router
