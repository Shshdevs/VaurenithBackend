from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.use_cases.environments import (
    CreateEnvironment,
    DeleteEnvironment,
    GetEnvironment,
    GetProjectEnvironments,
    UpdateEnvironment,
)
from app.application.projects.use_cases.project_devices import (
    DeleteProjectDevice,
    GetDeviceProjects,
    GetProjectDevice,
    GetProjectDevices,
    LinkProjectDevice,
    UpdateProjectDevice,
)
from app.application.projects.use_cases.projects import (
    CreateProject,
    DeleteProject,
    GetProject,
    GetUserProjects,
    UpdateProject,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers import (
    provide_create_environment,
    provide_create_project,
    provide_delete_environment,
    provide_delete_project,
    provide_delete_project_device,
    provide_get_device_projects,
    provide_get_environment,
    provide_get_project,
    provide_get_project_device,
    provide_get_project_devices,
    provide_get_project_environments,
    provide_get_user_projects,
    provide_link_project_device,
    provide_update_environment,
    provide_update_project,
    provide_update_project_device,
)


def get_create_project_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> CreateProject:
    return provide_create_project(session)


def get_get_project_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetProject:
    return provide_get_project(session)


def get_get_user_projects_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetUserProjects:
    return provide_get_user_projects(session)


def get_update_project_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> UpdateProject:
    return provide_update_project(session)


def get_delete_project_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> DeleteProject:
    return provide_delete_project(session)


def get_create_environment_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> CreateEnvironment:
    return provide_create_environment(session)


def get_get_environment_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetEnvironment:
    return provide_get_environment(session)


def get_get_project_environments_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetProjectEnvironments:
    return provide_get_project_environments(session)


def get_update_environment_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> UpdateEnvironment:
    return provide_update_environment(session)


def get_delete_environment_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> DeleteEnvironment:
    return provide_delete_environment(session)


def get_get_project_device_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetProjectDevice:
    return provide_get_project_device(session)


def get_get_project_devices_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetProjectDevices:
    return provide_get_project_devices(session)


def get_get_device_projects_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetDeviceProjects:
    return provide_get_device_projects(session)


def get_update_project_device_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> UpdateProjectDevice:
    return provide_update_project_device(session)


def get_link_project_device_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> LinkProjectDevice:
    return provide_link_project_device(session)


def get_delete_project_device_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> DeleteProjectDevice:
    return provide_delete_project_device(session)
