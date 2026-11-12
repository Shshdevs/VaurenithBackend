from fastapi import APIRouter

from app.api.routes.v1.relations import build_relations_entity_router
from app.api.routes.v1.relations.relation import build_relation_router
from app.bootstrap.dependencies.identity import get_authenticated_identity
from app.bootstrap.dependencies.relations import (
    create_relation_dependency,
    delete_relation_dependency,
    get_project_relations_dependency,
    get_relation_dependency,
    update_relation_dependency,
)


def build_relations_api_router() -> APIRouter:
    relation_router = build_relation_router(
        create_relation_dependency=create_relation_dependency,
        get_relation_dependency=get_relation_dependency,
        get_project_relations_dependency=get_project_relations_dependency,
        update_relation_dependency=update_relation_dependency,
        delete_relation_dependency=delete_relation_dependency,
        authenticated_identity_dependency=get_authenticated_identity,
    )
    router = APIRouter()
    router.include_router(build_relations_entity_router([relation_router]))
    return router
