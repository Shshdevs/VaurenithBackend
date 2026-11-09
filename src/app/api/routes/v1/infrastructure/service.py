from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1 import (
    ServiceCreateRequest,
    ServiceData,
    ServiceStatusUpdateRequest,
    ServiceUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.service import (
    CreateService,
    DeleteService,
    GetDeviceServices,
    GetEnvironmentServices,
    GetProjectServices,
    GetService,
    GetUserServices,
    UpdateService,
    UpdateServiceStatus,
)


def build_service_router(
    create_service_dependency: Callable[..., CreateService],
    get_service_dependency: Callable[..., GetService],
    get_user_services_dependency: Callable[..., GetUserServices],
    get_device_services_dependency: Callable[..., GetDeviceServices],
    get_project_services_dependency: Callable[..., GetProjectServices],
    get_environment_services_dependency: Callable[..., GetEnvironmentServices],
    update_service_dependency: Callable[..., UpdateService],
    update_service_status_dependency: Callable[..., UpdateServiceStatus],
    delete_service_dependency: Callable[..., DeleteService],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["services"])

    @router.get(
        "/services",
        response_model=ApiResponse[list[ServiceData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_user_services(
        get_user_services: GetUserServices = Depends(get_user_services_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ServiceData]]:
        services = await get_user_services.execute(identity)
        return ApiResponse[list[ServiceData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ServiceData.model_validate(service) for service in services],
        )

    @router.post(
        "/services",
        response_model=ApiResponse[ServiceData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create(
        request: ServiceCreateRequest,
        create_service: CreateService = Depends(create_service_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ServiceData]:
        service = await create_service.execute(identity=identity, **request.model_dump())
        return ApiResponse[ServiceData](
            status=format_http_status(status.HTTP_201_CREATED),
            message="Service is created successfully",
            data=ServiceData.model_validate(service),
        )

    @router.get(
        "/services/{service_id}",
        response_model=ApiResponse[ServiceData],
        status_code=status.HTTP_200_OK,
    )
    async def get_service(
        service_id: UUID,
        get_service: GetService = Depends(get_service_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ServiceData]:
        service = await get_service.execute(identity, service_id)
        return ApiResponse[ServiceData](
            status=format_http_status(status.HTTP_200_OK),
            data=ServiceData.model_validate(service),
        )

    @router.get(
        "/devices/{device_id}/services",
        response_model=ApiResponse[list[ServiceData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_device_services(
        device_id: UUID,
        get_device_services: GetDeviceServices = Depends(get_device_services_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ServiceData]]:
        services = await get_device_services.execute(identity, device_id)
        return ApiResponse[list[ServiceData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ServiceData.model_validate(service) for service in services],
        )

    @router.get(
        "/projects/{project_id}/services",
        response_model=ApiResponse[list[ServiceData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_project_services(
        project_id: UUID,
        get_project_services: GetProjectServices = Depends(get_project_services_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ServiceData]]:
        services = await get_project_services.execute(identity, project_id)
        return ApiResponse[list[ServiceData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ServiceData.model_validate(service) for service in services],
        )

    @router.get(
        "/environments/{environment_id}/services",
        response_model=ApiResponse[list[ServiceData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_environment_services(
        environment_id: UUID,
        get_environment_services: GetEnvironmentServices = Depends(
            get_environment_services_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ServiceData]]:
        services = await get_environment_services.execute(identity, environment_id)
        return ApiResponse[list[ServiceData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[ServiceData.model_validate(service) for service in services],
        )

    @router.put(
        "/services/{service_id}",
        response_model=ApiResponse[ServiceData],
        status_code=status.HTTP_200_OK,
    )
    async def update(
        service_id: UUID,
        request: ServiceUpdateRequest,
        update_service: UpdateService = Depends(update_service_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ServiceData]:
        request_data = request.model_dump()
        expected_version = request_data.pop("version")
        service = await update_service.execute(
            identity=identity,
            service_id=service_id,
            expected_version=expected_version,
            **request_data,
        )
        return ApiResponse[ServiceData](
            status=format_http_status(status.HTTP_200_OK),
            message="Service is updated successfully",
            data=ServiceData.model_validate(service),
        )

    @router.patch(
        "/services/{service_id}/status",
        response_model=ApiResponse[ServiceData],
        status_code=status.HTTP_200_OK,
    )
    async def update_status(
        service_id: UUID,
        request: ServiceStatusUpdateRequest,
        update_service_status: UpdateServiceStatus = Depends(
            update_service_status_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ServiceData]:
        service = await update_service_status.execute(
            identity=identity,
            service_id=service_id,
            expected_version=request.version,
            status=request.status,
        )
        return ApiResponse[ServiceData](
            status=format_http_status(status.HTTP_200_OK),
            message="Service status is updated successfully",
            data=ServiceData.model_validate(service),
        )

    @router.delete(
        "/services/{service_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_service(
        service_id: UUID,
        delete_service: DeleteService = Depends(delete_service_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_service.execute(identity, service_id)
        return ApiResponse[None](status=format_http_status(status.HTTP_200_OK))

    return router
