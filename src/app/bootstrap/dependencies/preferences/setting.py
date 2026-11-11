from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.preferences.use_cases.setting import (
    CreateSetting,
    DeleteSetting,
    GetSetting,
    GetSettings,
    UpdateSetting,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.preferences import (
    provide_create_setting,
    provide_delete_setting,
    provide_get_setting,
    provide_get_settings,
    provide_update_setting,
)


def get_settings_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetSettings:
    return provide_get_settings(session)


def get_setting_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetSetting:
    return provide_get_setting(session)


def create_setting_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateSetting:
    return provide_create_setting(session)


def update_setting_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateSetting:
    return provide_update_setting(session)


def delete_setting_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteSetting:
    return provide_delete_setting(session)
