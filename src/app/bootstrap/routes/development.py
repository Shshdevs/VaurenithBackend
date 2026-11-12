from fastapi import APIRouter

from app.api.routes.v1.development import build_development_entity_router
from app.api.routes.v1.development.branch import build_branch_router
from app.api.routes.v1.development.code_component import build_code_component_router
from app.api.routes.v1.development.commit import build_commit_router
from app.api.routes.v1.development.dependency import build_dependency_router
from app.api.routes.v1.development.repository import build_repository_router
from app.bootstrap.dependencies.development import (
    create_branch_dependency,
    create_code_component_dependency,
    create_commit_dependency,
    create_dependency_dependency,
    create_repository_dependency,
    delete_branch_dependency,
    delete_code_component_dependency,
    delete_dependency_dependency,
    delete_repository_dependency,
    get_branch_dependency,
    get_code_component_dependency,
    get_commit_dependency,
    get_component_dependencies_dependency,
    get_dependency_dependency,
    get_project_repositories_dependency,
    get_repository_branches_dependency,
    get_repository_code_components_dependency,
    get_repository_commits_dependency,
    get_repository_dependencies_dependency,
    get_repository_dependency,
    get_user_repositories_dependency,
    update_branch_dependency,
    update_code_component_dependency,
    update_dependency_dependency,
    update_repository_dependency,
)
from app.bootstrap.dependencies.identity import get_authenticated_identity


def build_development_api_router() -> APIRouter:
    entity_routers = [
        build_repository_router(
            create_repository_dependency=create_repository_dependency,
            get_repository_dependency=get_repository_dependency,
            get_user_repositories_dependency=get_user_repositories_dependency,
            get_project_repositories_dependency=get_project_repositories_dependency,
            update_repository_dependency=update_repository_dependency,
            delete_repository_dependency=delete_repository_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        ),
        build_branch_router(
            create_branch_dependency=create_branch_dependency,
            get_branch_dependency=get_branch_dependency,
            get_repository_branches_dependency=get_repository_branches_dependency,
            update_branch_dependency=update_branch_dependency,
            delete_branch_dependency=delete_branch_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        ),
        build_code_component_router(
            create_code_component_dependency=create_code_component_dependency,
            get_code_component_dependency=get_code_component_dependency,
            get_repository_code_components_dependency=get_repository_code_components_dependency,
            update_code_component_dependency=update_code_component_dependency,
            delete_code_component_dependency=delete_code_component_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        ),
        build_commit_router(
            create_commit_dependency=create_commit_dependency,
            get_commit_dependency=get_commit_dependency,
            get_repository_commits_dependency=get_repository_commits_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        ),
        build_dependency_router(
            create_dependency_dependency=create_dependency_dependency,
            get_dependency_dependency=get_dependency_dependency,
            get_component_dependencies_dependency=get_component_dependencies_dependency,
            get_repository_dependencies_dependency=get_repository_dependencies_dependency,
            update_dependency_dependency=update_dependency_dependency,
            delete_dependency_dependency=delete_dependency_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        ),
    ]
    router = APIRouter()
    router.include_router(build_development_entity_router(entity_routers))
    return router
