from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.response import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.infrastructure import (
    DeviceGroup,
    DeviceGroupCreateRequest,
    DeviceGroupMemberCreateRequest,
    DeviceGroupMemberData,
    DeviceGroupUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.device_group import (
    AddDeviceGroupMember,
    CreateDeviceGroup,
    DeleteDeviceGroup,
    GetDeviceGroup,
    GetDeviceGroupMembers,
    GetUserDeviceGroups,
    RemoveDeviceGroupMember,
    UpdateDeviceGroup,
)
from app.domain.common.enums import EntityType


def build_device_group_router(
    create_device_group_dependency: Callable[..., CreateDeviceGroup],
    get_device_group_dependency: Callable[..., GetDeviceGroup],
    get_user_device_groups_dependency: Callable[..., GetUserDeviceGroups],
    get_device_group_members_dependency: Callable[..., GetDeviceGroupMembers],
    add_device_group_member_dependency: Callable[..., AddDeviceGroupMember],
    remove_device_group_member_dependency: Callable[..., RemoveDeviceGroupMember],
    delete_device_group_dependency: Callable[..., DeleteDeviceGroup],
    update_device_group_dependency: Callable[..., UpdateDeviceGroup],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["device_groups"])

    @router.get(
        "/device-groups/{device_group_id}/members",
        response_model=ApiResponse[list[DeviceGroupMemberData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_members(
        device_group_id: UUID,
        get_members_use_case: GetDeviceGroupMembers = Depends(
            get_device_group_members_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[DeviceGroupMemberData]]:
        members = await get_members_use_case.list_members(identity, device_group_id)
        return ApiResponse[list[DeviceGroupMemberData]](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.DEVICE_GROUP,
            data=[DeviceGroupMemberData.model_validate(member) for member in members],
        )

    @router.post(
        "/device-groups/{device_group_id}/members",
        response_model=ApiResponse[DeviceGroupMemberData],
        status_code=status.HTTP_201_CREATED,
    )
    async def add_member(
        device_group_id: UUID,
        request: DeviceGroupMemberCreateRequest,
        add_member_use_case: AddDeviceGroupMember = Depends(
            add_device_group_member_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DeviceGroupMemberData]:
        member = await add_member_use_case.add(identity, device_group_id, request.device_id)
        return ApiResponse[DeviceGroupMemberData](
            status=format_http_status(status.HTTP_201_CREATED),
            code=ResponseCode.ADDED,
            entity_type=EntityType.DEVICE_GROUP,
            data=DeviceGroupMemberData.model_validate(member),
        )

    @router.delete(
        "/device-groups/{device_group_id}/members/{device_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def remove_member(
        device_group_id: UUID,
        device_id: UUID,
        remove_member_use_case: RemoveDeviceGroupMember = Depends(
            remove_device_group_member_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await remove_member_use_case.remove(identity, device_group_id, device_id)
        return ApiResponse[None](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.REMOVED,
            entity_type=EntityType.DEVICE_GROUP,
        )

    @router.get(
        "/device-groups",
        response_model=ApiResponse[list[DeviceGroup]],
        status_code=status.HTTP_200_OK,
    )
    async def get_user_device_groups(
        get_user_device_groups: GetUserDeviceGroups = Depends(
            get_user_device_groups_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[DeviceGroup]]:
        groups = await get_user_device_groups.execute(identity)
        return ApiResponse[list[DeviceGroup]](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.DEVICE_GROUP,
            data=[DeviceGroup.model_validate(group) for group in groups],
        )

    @router.post(
        "/device-groups",
        response_model=ApiResponse[DeviceGroup],
        status_code=status.HTTP_201_CREATED,
    )
    async def create(
        request: DeviceGroupCreateRequest,
        create_device_group: CreateDeviceGroup = Depends(create_device_group_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DeviceGroup]:
        device_group = await create_device_group.execute(
            identity=identity, name=request.name, description=request.description
        )
        return ApiResponse[DeviceGroup](
            status=format_http_status(status.HTTP_201_CREATED),
            code=ResponseCode.CREATED,
            entity_type=EntityType.DEVICE_GROUP,
            data=DeviceGroup.model_validate(device_group),
        )

    @router.get(
        "/device-groups/{device_group_id}",
        response_model=ApiResponse[DeviceGroup],
        status_code=status.HTTP_200_OK,
    )
    async def get_device_group(
        device_group_id: UUID,
        get_device_group: GetDeviceGroup = Depends(get_device_group_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DeviceGroup]:
        device_group = await get_device_group.execute(
            identity=identity, device_group_id=device_group_id
        )
        return ApiResponse[DeviceGroup](
            status=format_http_status(status.HTTP_200_OK),
            data=DeviceGroup.model_validate(device_group),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.DEVICE,
        )

    @router.put(
        "/device-groups/{device_group_id}",
        response_model=ApiResponse[DeviceGroup],
        status_code=status.HTTP_200_OK,
    )
    async def update(
        device_group_id: UUID,
        request: DeviceGroupUpdateRequest,
        update_device_group: UpdateDeviceGroup = Depends(update_device_group_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[DeviceGroup]:
        device_group = await update_device_group.execute(
            identity=identity,
            device_group_id=device_group_id,
            name=request.name,
            description=request.description,
            expected_version=request.version,
        )

        return ApiResponse[DeviceGroup](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.UPDATED,
            entity_type=EntityType.DEVICE_GROUP,
            data=DeviceGroup.model_validate(device_group),
        )

    @router.delete(
        "/device-groups/{device_group_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_device_group(
        device_group_id: UUID,
        delete_device_group: DeleteDeviceGroup = Depends(delete_device_group_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await delete_device_group.execute(
            identity=identity, device_group_id=device_group_id
        )
        return ApiResponse[None](
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.DELETED,
            entity_type=None,
        )

    return router
