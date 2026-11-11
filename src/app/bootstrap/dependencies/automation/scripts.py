from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.automation import (
    CreateScript,
    DeleteScript,
    GetScript,
    GetUserScripts,
    UpdateScript,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.automation import (
    provide_create_script,
    provide_delete_script,
    provide_get_script,
    provide_get_user_scripts,
    provide_update_script,
)


def create_automation_script_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateScript:
    return provide_create_script(session)


def get_automation_script_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetScript:
    return provide_get_script(session)


def get_user_automation_scripts_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetUserScripts:
    return provide_get_user_scripts(session)


def update_automation_script_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateScript:
    return provide_update_script(session)


def delete_automation_script_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteScript:
    return provide_delete_script(session)
