from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.use_cases.project_devices import (
    DeleteProjectDevice,
    GetDeviceProjects,
    GetProjectDevice,
    GetProjectDevices,
    LinkProjectDevice,
    UpdateProjectDevice,
)
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyProjectDeviceRepository,
    SqlAlchemyProjectRepository,
)


def provide_link_project_device(session: AsyncSession) -> LinkProjectDevice:
    return LinkProjectDevice(
        SqlAlchemyProjectDeviceRepository(session), SqlAlchemyProjectRepository(session)
    )


def provide_update_project_device(session: AsyncSession) -> UpdateProjectDevice:
    return UpdateProjectDevice(
        SqlAlchemyProjectDeviceRepository(session), SqlAlchemyProjectRepository(session)
    )


def provide_delete_project_device(session: AsyncSession) -> DeleteProjectDevice:
    return DeleteProjectDevice(
        SqlAlchemyProjectDeviceRepository(session), SqlAlchemyProjectRepository(session)
    )


def provide_get_device_projects(session: AsyncSession) -> GetDeviceProjects:
    return GetDeviceProjects(
        SqlAlchemyProjectDeviceRepository(session), SqlAlchemyProjectRepository(session)
    )


def provide_get_project_device(session: AsyncSession) -> GetProjectDevice:
    return GetProjectDevice(
        SqlAlchemyProjectDeviceRepository(session), SqlAlchemyProjectRepository(session)
    )


def provide_get_project_devices(session: AsyncSession) -> GetProjectDevices:
    return GetProjectDevices(
        SqlAlchemyProjectDeviceRepository(session), SqlAlchemyProjectRepository(session)
    )


__all__ = [
    "provide_link_project_device",
    "provide_update_project_device",
    "provide_delete_project_device",
    "provide_get_device_projects",
    "provide_get_project_device",
    "provide_get_project_devices",
]
