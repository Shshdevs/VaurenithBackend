from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.use_cases.project_devices import (
    DeleteProjectDevice,
    GetDeviceProjects,
    GetProjectDevice,
    GetProjectDevices,
    LinkProjectDevice,
    UpdateProjectDevice,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.projects import (
    provide_delete_project_device,
    provide_get_device_projects,
    provide_get_project_device,
    provide_get_project_devices,
    provide_link_project_device,
    provide_update_project_device,
)


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


__all__ = [
    "get_get_project_device_dependency",
    "get_get_project_devices_dependency",
    "get_get_device_projects_dependency",
    "get_update_project_device_dependency",
    "get_link_project_device_dependency",
    "get_delete_project_device_dependency",
]
