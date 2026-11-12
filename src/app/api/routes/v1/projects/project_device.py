from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.projects import (
    ProjectDeviceCreateRequest,
    ProjectDeviceData,
    ProjectDeviceUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.projects.use_cases.project_devices import (
    DeleteProjectDevice,
    GetDeviceProjects,
    GetProjectDevice,
    GetProjectDevices,
    LinkProjectDevice,
    UpdateProjectDevice,
)
from app.domain.common.enums import EntityType


def build_project_device_route(
    get_project_device_dependency: Callable[..., GetProjectDevice],
    get_project_devices_dependency: Callable[..., GetProjectDevices],
    get_device_projects_dependency: Callable[..., GetDeviceProjects],
    link_project_device_dependency: Callable[..., LinkProjectDevice],
    update_project_device_dependency: Callable[..., UpdateProjectDevice],
    delete_project_device_dependency: Callable[..., DeleteProjectDevice],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["project_devices"])

    @router.get(
        "/project_devices/{project_device_id}",
        response_model=ApiResponse[ProjectDeviceData],
        status_code=status.HTTP_200_OK,
    )
    async def get_project_device(
        project_device_id: UUID,
        get_project_device: GetProjectDevice = Depends(get_project_device_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ProjectDeviceData]:
        result = await get_project_device.execute(
            identity=identity, project_device_id=project_device_id
        )

        return ApiResponse[ProjectDeviceData](
            status=format_http_status(status.HTTP_200_OK),
            data=ProjectDeviceData.model_validate(result),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.PROJECT_DEVICE,
        )

    @router.get(
        "/projects/{project_id}/devices",
        response_model=ApiResponse[list[ProjectDeviceData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_project_devices(
        project_id: UUID,
        get_project_devices: GetProjectDevices = Depends(get_project_devices_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ProjectDeviceData]]:
        result = await get_project_devices.execute(identity=identity, project_id=project_id)

        return ApiResponse[list[ProjectDeviceData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ProjectDeviceData.model_validate(model) for model in result],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.PROJECT_DEVICE,
        )

    @router.get(
        "/devices/{device_id}/projects",
        response_model=ApiResponse[list[ProjectDeviceData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_devices_project(
        device_id: UUID,
        get_device_projects: GetDeviceProjects = Depends(get_device_projects_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ProjectDeviceData]]:
        result = await get_device_projects.execute(identity=identity, device_id=device_id)

        return ApiResponse[list[ProjectDeviceData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ProjectDeviceData.model_validate(model) for model in result],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.PROJECT_DEVICE,
        )

    @router.post(
        "/project_devices",
        response_model=ApiResponse[ProjectDeviceData],
        status_code=status.HTTP_201_CREATED,
    )
    async def link_project_device(
        request: ProjectDeviceCreateRequest,
        link_project_device: LinkProjectDevice = Depends(link_project_device_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ProjectDeviceData]:
        result = await link_project_device.execute(
            identity=identity,
            project_id=request.project_id,
            device_id=request.device_id,
            role=request.role,
        )
        return ApiResponse[ProjectDeviceData](
            status=format_http_status(status.HTTP_201_CREATED),
            code=ResponseCode.CREATED,
            entity_type=EntityType.PROJECT_DEVICE,
            data=ProjectDeviceData.model_validate(result),
        )

    @router.put(
        "/project_devices/{project_device_id}",
        response_model=ApiResponse[ProjectDeviceData],
        status_code=status.HTTP_200_OK,
    )
    async def update_project(
        project_device_id: UUID,
        request: ProjectDeviceUpdateRequest,
        update_project_device: UpdateProjectDevice = Depends(
            update_project_device_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ProjectDeviceData]:
        result = await update_project_device.execute(
            identity=identity,
            project_device_id=project_device_id,
            project_id=request.project_id,
            device_id=request.device_id,
            role=request.role,
        )

        return ApiResponse[ProjectDeviceData](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.UPDATED,
            entity_type=EntityType.PROJECT_DEVICE,
            data=ProjectDeviceData.model_validate(result),
        )

    @router.delete(
        "/project_devices/{project_device_id}",
        response_model=ApiResponse[ProjectDeviceData],
        status_code=status.HTTP_200_OK,
    )
    async def delete_project(
        project_device_id: UUID,
        delete_project_device: DeleteProjectDevice = Depends(
            delete_project_device_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_project_device.execute(
            identity=identity, project_device_id=project_device_id
        )
        return ApiResponse[None](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.DELETED,
            entity_type=EntityType.PROJECT_DEVICE,
            data=None,
        )

    return router
