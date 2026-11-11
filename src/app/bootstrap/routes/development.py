from fastapi import APIRouter

from app.api.routes.v1.development.repository import build_repository_router
from app.bootstrap.dependencies.development import (
    create_repository_dependency,
    delete_repository_dependency,
    get_project_repositories_dependency,
    get_repository_dependency,
    get_user_repositories_dependency,
    update_repository_dependency,
)
from app.bootstrap.dependencies.identity import get_authenticated_identity


def build_development_api_router() -> APIRouter:
    return build_repository_router(
        create_repository_dependency=create_repository_dependency,
        get_repository_dependency=get_repository_dependency,
        get_user_repositories_dependency=get_user_repositories_dependency,
        get_project_repositories_dependency=get_project_repositories_dependency,
        update_repository_dependency=update_repository_dependency,
        delete_repository_dependency=delete_repository_dependency,
        authenticated_identity_dependency=get_authenticated_identity,
    )
