from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.response import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.relations import (
    RelationCreateRequest,
    RelationData,
    RelationUpdateRequest,
)
from app.application.identity import VerifiedIdentity
from app.application.relations import (
    CreateRelation,
    DeleteRelation,
    GetProjectRelations,
    GetRelation,
    UpdateRelation,
)
from app.domain.common.enums import EntityType


def build_relation_router(
    create_relation_dependency: Callable[..., CreateRelation],
    get_relation_dependency: Callable[..., GetRelation],
    get_project_relations_dependency: Callable[..., GetProjectRelations],
    update_relation_dependency: Callable[..., UpdateRelation],
    delete_relation_dependency: Callable[..., DeleteRelation],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["relations"])

    @router.post(
        "/projects/{project_id}/relations",
        response_model=ApiResponse[RelationData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_relation(
        project_id: UUID,
        request: RelationCreateRequest,
        use_case: CreateRelation = Depends(create_relation_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[RelationData]:
        relation = await use_case.execute(
            identity=identity,
            project_id=project_id,
            **request.model_dump(),
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            code=ResponseCode.CREATED,
            entity_type=EntityType.RELATION,
            data=RelationData.model_validate(relation),
        )

    @router.get(
        "/projects/{project_id}/relations",
        response_model=ApiResponse[list[RelationData]],
        status_code=status.HTTP_200_OK,
    )
    async def get_project_relations(
        project_id: UUID,
        entity_type: EntityType | None = Query(default=None),
        entity_id: UUID | None = Query(default=None),
        use_case: GetProjectRelations = Depends(get_project_relations_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[RelationData]]:
        relations = await use_case.execute(
            identity=identity,
            project_id=project_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[RelationData.model_validate(item) for item in relations],
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.RELATION,
        )

    @router.get(
        "/projects/{project_id}/relations/{relation_id}",
        response_model=ApiResponse[RelationData],
        status_code=status.HTTP_200_OK,
    )
    async def get_relation(
        project_id: UUID,
        relation_id: UUID,
        use_case: GetRelation = Depends(get_relation_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[RelationData]:
        relation = await use_case.execute(identity, project_id, relation_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=RelationData.model_validate(relation),
            code=ResponseCode.RETRIEVED,
            entity_type=EntityType.RELATION,
        )

    @router.put(
        "/projects/{project_id}/relations/{relation_id}",
        response_model=ApiResponse[RelationData],
        status_code=status.HTTP_200_OK,
    )
    async def update_relation(
        project_id: UUID,
        relation_id: UUID,
        request: RelationUpdateRequest,
        use_case: UpdateRelation = Depends(update_relation_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[RelationData]:
        relation = await use_case.execute(
            identity=identity,
            project_id=project_id,
            relation_id=relation_id,
            **request.model_dump(),
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.UPDATED,
            entity_type=EntityType.RELATION,
            data=RelationData.model_validate(relation),
        )

    @router.delete(
        "/projects/{project_id}/relations/{relation_id}",
        response_model=ApiResponse[None],
        status_code=status.HTTP_200_OK,
    )
    async def delete_relation(
        project_id: UUID,
        relation_id: UUID,
        use_case: DeleteRelation = Depends(delete_relation_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await use_case.execute(identity, project_id, relation_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            code=ResponseCode.DELETED,
            entity_type=EntityType.RELATION,
            data=None,
        )

    return router
