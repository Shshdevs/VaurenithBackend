from fastapi import APIRouter

from app.api.routes.v1.projects.project import build_project_route
from app.bootstrap.dependencies.identity import get_authenticated_identity
from app.bootstrap.dependencies.projects import get_create_project_dependency


def build_projects_api_router() -> APIRouter:
    return build_project_route(
        create_project_dependency=get_create_project_dependency,
        authenticated_identity_dependency=get_authenticated_identity,
    )
