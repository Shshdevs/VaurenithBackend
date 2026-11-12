from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.infrastructure import (
    DatabaseCreateRequest,
    DatabaseData,
    DatabaseUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.database import (
    CreateDatabase,
    DeleteDatabase,
    GetDatabase,
    GetDatabasesByContainer,
    GetDatabasesByDevice,
    GetDatabasesByEnvironment,
    GetDatabasesByProject,
    GetDatabasesByService,
    GetUserDatabases,
    UpdateDatabase,
)
from app.domain.common.enums import EntityType


def build_database_router(
    create_database_dependency: Callable[..., CreateDatabase],
    get_database_dependency: Callable[..., GetDatabase],
    get_user_databases_dependency: Callable[..., GetUserDatabases],
    get_device_databases_dependency: Callable[..., GetDatabasesByDevice],
    get_project_databases_dependency: Callable[..., GetDatabasesByProject],
    get_environment_databases_dependency: Callable[..., GetDatabasesByEnvironment],
    get_container_databases_dependency: Callable[..., GetDatabasesByContainer],
    get_service_databases_dependency: Callable[..., GetDatabasesByService],
    update_database_dependency: Callable[..., UpdateDatabase],
    delete_database_dependency: Callable[..., DeleteDatabase],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["databases"])

    @router.post(
        "/databases",
        response_model=ApiResponse[DatabaseData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create(
        request: DatabaseCreateRequest,
        create_database: CreateDatabase = Depends(create_database_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DatabaseData]:
        database = await create_database.execute(identity=identity, **request.model_dump())
        return ApiResponse[DatabaseData](
            status=format_http_status(status.HTTP_201_CREATED),
            code=ResponseCode.CREATED,
            entity_type=EntityType.DATABASE,
            data=DatabaseData.model_validate(database),
        )

    @router.get(
        "/databases",
        response_model=ApiResponse[list[DatabaseData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_user_databases(
        get_user_databases: GetUserDatabases = Depends(get_user_databases_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[DatabaseData]]:
        databases = await get_user_databases.execute(identity)
        return ApiResponse[list[DatabaseData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[DatabaseData.model_validate(database) for database in databases],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.DATABASE,
        )

    @router.get(
        "/databases/{database_id}",
        response_model=ApiResponse[DatabaseData],
        status_code=status.HTTP_200_OK,
    )
    async def get_database(
        database_id: UUID,
        get_database: GetDatabase = Depends(get_database_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DatabaseData]:
        database = await get_database.execute(identity, database_id)
        return ApiResponse[DatabaseData](
            status=format_http_status(status.HTTP_200_OK),
            data=DatabaseData.model_validate(database),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.DATABASE,
        )

    @router.get(
        "/devices/{device_id}/databases",
        response_model=ApiResponse[list[DatabaseData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_device_databases(
        device_id: UUID,
        get_device_databases: GetDatabasesByDevice = Depends(
            get_device_databases_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[DatabaseData]]:
        databases = await get_device_databases.execute(identity, device_id)
        return ApiResponse[list[DatabaseData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[DatabaseData.model_validate(database) for database in databases],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.DATABASE,
        )

    @router.get(
        "/projects/{project_id}/databases",
        response_model=ApiResponse[list[DatabaseData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_project_databases(
        project_id: UUID,
        get_project_databases: GetDatabasesByProject = Depends(
            get_project_databases_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[DatabaseData]]:
        databases = await get_project_databases.execute(identity, project_id)
        return ApiResponse[list[DatabaseData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[DatabaseData.model_validate(database) for database in databases],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.DATABASE,
        )

    @router.get(
        "/environments/{environment_id}/databases",
        response_model=ApiResponse[list[DatabaseData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_environment_databases(
        environment_id: UUID,
        get_environment_databases: GetDatabasesByEnvironment = Depends(
            get_environment_databases_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[DatabaseData]]:
        databases = await get_environment_databases.execute(identity, environment_id)
        return ApiResponse[list[DatabaseData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[DatabaseData.model_validate(database) for database in databases],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.DATABASE,
        )

    @router.get(
        "/containers/{container_id}/databases",
        response_model=ApiResponse[list[DatabaseData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_container_databases(
        container_id: UUID,
        get_container_databases: GetDatabasesByContainer = Depends(
            get_container_databases_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[DatabaseData]]:
        databases = await get_container_databases.execute(identity, container_id)
        return ApiResponse[list[DatabaseData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[DatabaseData.model_validate(database) for database in databases],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.DATABASE,
        )

    @router.get(
        "/services/{service_id}/databases",
        response_model=ApiResponse[list[DatabaseData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_service_databases(
        service_id: UUID,
        get_service_databases: GetDatabasesByService = Depends(
            get_service_databases_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[DatabaseData]]:
        databases = await get_service_databases.execute(identity, service_id)
        return ApiResponse[list[DatabaseData]](
            status=format_http_status(status.HTTP_200_OK),
            data=[DatabaseData.model_validate(database) for database in databases],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.DATABASE,
        )

    @router.put(
        "/databases/{database_id}",
        response_model=ApiResponse[DatabaseData],
        status_code=status.HTTP_200_OK,
    )
    async def update(
        database_id: UUID,
        request: DatabaseUpdateRequest,
        update_database: UpdateDatabase = Depends(update_database_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DatabaseData]:
        request_data = request.model_dump()
        expected_version = request_data.pop("version")
        database = await update_database.execute(
            identity=identity,
            database_id=database_id,
            expected_version=expected_version,
            **request_data,
        )
        return ApiResponse[DatabaseData](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.UPDATED,
            entity_type=EntityType.DATABASE,
            data=DatabaseData.model_validate(database),
        )

    @router.delete(
        "/databases/{database_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_database(
        database_id: UUID,
        delete_database: DeleteDatabase = Depends(delete_database_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_database.execute(identity, database_id)
        return ApiResponse[None](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.DELETED,
            entity_type=None,
        )

    return router
