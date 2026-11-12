from fastapi import APIRouter

from app.api.routes.v1.development.code_component import build_code_component_router
from app.api.routes.v1.development.repository import build_repository_router
from app.bootstrap.dependencies.development import (
    create_code_component_dependency,
    create_repository_dependency,
    delete_code_component_dependency,
    delete_repository_dependency,
    get_code_component_dependency,
    get_project_repositories_dependency,
    get_repository_code_components_dependency,
    get_repository_dependency,
    get_user_repositories_dependency,
    update_code_component_dependency,
    update_repository_dependency,
)
from app.bootstrap.dependencies.identity import get_authenticated_identity


def build_development_api_router() -> APIRouter:
    router = build_repository_router(
        create_repository_dependency=create_repository_dependency,
        get_repository_dependency=get_repository_dependency,
        get_user_repositories_dependency=get_user_repositories_dependency,
        get_project_repositories_dependency=get_project_repositories_dependency,
        update_repository_dependency=update_repository_dependency,
        delete_repository_dependency=delete_repository_dependency,
        authenticated_identity_dependency=get_authenticated_identity,
    )
    router.include_router(
        build_code_component_router(
            create_code_component_dependency=create_code_component_dependency,
            get_code_component_dependency=get_code_component_dependency,
            get_repository_code_components_dependency=get_repository_code_components_dependency,
            update_code_component_dependency=update_code_component_dependency,
            delete_code_component_dependency=delete_code_component_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )
    return router
