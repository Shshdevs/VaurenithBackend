from fastapi import APIRouter

from app.api.routes.v1.projects.environment import build_environment_route
from app.api.routes.v1.projects.project import build_project_route
from app.bootstrap.dependencies.identity import get_authenticated_identity
from app.bootstrap.dependencies.projects import (
    get_create_environment_dependency,
    get_create_project_dependency,
    get_delete_environment_dependency,
    get_delete_project_dependency,
    get_get_environment_dependency,
    get_get_project_dependency,
    get_get_project_environments_dependency,
    get_get_user_projects_dependency,
    get_update_environment_dependency,
    get_update_project_dependency,
)


def build_projects_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(
        build_project_route(
            create_project_dependency=get_create_project_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
            get_project_dependency=get_get_project_dependency,
            get_user_projects_dependency=get_get_user_projects_dependency,
            update_project_dependency=get_update_project_dependency,
            delete_project_dependency=get_delete_project_dependency,
        )
    )
    router.include_router(
        build_environment_route(
            create_environment_dependency=get_create_environment_dependency,
            get_environment_dependency=get_get_environment_dependency,
            get_project_environments_dependency=get_get_project_environments_dependency,
            update_environment_dependency=get_update_environment_dependency,
            delete_environment_dependency=get_delete_environment_dependency,
            get_project_dependency=get_get_project_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )
    return router
