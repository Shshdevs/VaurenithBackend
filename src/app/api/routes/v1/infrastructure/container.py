from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.infrastructure import (
    ContainerCreateRequest,
    ContainerData,
    ContainerUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.container import (
    CreateContainer,
    DeleteContainer,
    GetContainer,
    GetContainersByProject,
    GetDeviceContainers,
    GetEnvironmentContainers,
    GetServiceContainers,
    GetUserContainers,
    UpdateContainer,
)
from app.domain.common.enums import EntityType


def build_container_router(
    create_container_dependency: Callable[..., CreateContainer],
    get_container_dependency: Callable[..., GetContainer],
    get_user_containers_dependency: Callable[..., GetUserContainers],
    get_device_containers_dependency: Callable[..., GetDeviceContainers],
    get_project_containers_dependency: Callable[..., GetContainersByProject],
    get_environment_containers_dependency: Callable[..., GetEnvironmentContainers],
    get_service_containers_dependency: Callable[..., GetServiceContainers],
    update_container_dependency: Callable[..., UpdateContainer],
    delete_container_dependency: Callable[..., DeleteContainer],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["containers"])

    @router.post(
        "/containers",
        response_model=ApiResponse[ContainerData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create(
        request: ContainerCreateRequest,
        create_container: CreateContainer = Depends(create_container_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ContainerData]:
        container = await create_container.execute(
            identity=identity, **request.model_dump()
        )
        return ApiResponse[ContainerData](
            status=format_http_status(status.HTTP_201_CREATED),
            code=ResponseCode.CREATED,
            entity_type=EntityType.CONTAINER,
            data=ContainerData.model_validate(container),
        )

    @router.get(
        "/containers",
        response_model=ApiResponse[list[ContainerData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_user_containers(
        get_user_containers: GetUserContainers = Depends(get_user_containers_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ContainerData]]:
        containers = await get_user_containers.execute(identity)
        return ApiResponse[list[ContainerData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ContainerData.model_validate(container) for container in containers],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.CONTAINER,
        )

    @router.get(
        "/containers/{container_id}",
        response_model=ApiResponse[ContainerData],
        status_code=status.HTTP_200_OK,
    )
    async def get_container(
        container_id: UUID,
        get_container: GetContainer = Depends(get_container_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ContainerData]:
        container = await get_container.execute(identity, container_id)
        return ApiResponse[ContainerData](
            status=format_http_status(status.HTTP_200_OK),
            data=ContainerData.model_validate(container),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.CONTAINER,
        )

    @router.get(
        "/devices/{device_id}/containers",
        response_model=ApiResponse[list[ContainerData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_device_containers(
        device_id: UUID,
        get_device_containers: GetDeviceContainers = Depends(
            get_device_containers_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ContainerData]]:
        containers = await get_device_containers.execute(identity, device_id)
        return ApiResponse[list[ContainerData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ContainerData.model_validate(container) for container in containers],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.CONTAINER,
        )

    @router.get(
        "/projects/{project_id}/containers",
        response_model=ApiResponse[list[ContainerData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_project_containers(
        project_id: UUID,
        get_project_containers: GetContainersByProject = Depends(
            get_project_containers_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ContainerData]]:
        containers = await get_project_containers.execute(identity, project_id)
        return ApiResponse[list[ContainerData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ContainerData.model_validate(container) for container in containers],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.CONTAINER,
        )

    @router.get(
        "/environments/{environment_id}/containers",
        response_model=ApiResponse[list[ContainerData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_environment_containers(
        environment_id: UUID,
        get_environment_containers: GetEnvironmentContainers = Depends(
            get_environment_containers_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ContainerData]]:
        containers = await get_environment_containers.execute(identity, environment_id)
        return ApiResponse[list[ContainerData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ContainerData.model_validate(container) for container in containers],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.CONTAINER,
        )

    @router.get(
        "/services/{service_id}/containers",
        response_model=ApiResponse[list[ContainerData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_service_containers(
        service_id: UUID,
        get_service_containers: GetServiceContainers = Depends(
            get_service_containers_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ContainerData]]:
        containers = await get_service_containers.execute(identity, service_id)
        return ApiResponse[list[ContainerData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ContainerData.model_validate(container) for container in containers],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.CONTAINER,
        )

    @router.put(
        "/containers/{container_id}",
        response_model=ApiResponse[ContainerData],
        status_code=status.HTTP_200_OK,
    )
    async def update(
        container_id: UUID,
        request: ContainerUpdateRequest,
        update_container: UpdateContainer = Depends(update_container_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ContainerData]:
        request_data = request.model_dump()
        expected_version = request_data.pop("version")
        container = await update_container.execute(
            identity=identity,
            container_id=container_id,
            expected_version=expected_version,
            **request_data,
        )
        return ApiResponse[ContainerData](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.UPDATED,
            entity_type=EntityType.CONTAINER,
            data=ContainerData.model_validate(container),
        )

    @router.delete(
        "/containers/{container_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_container(
        container_id: UUID,
        delete_container: DeleteContainer = Depends(delete_container_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_container.execute(identity, container_id)
        return ApiResponse[None](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.DELETED,
            entity_type=None,
        )

    return router
