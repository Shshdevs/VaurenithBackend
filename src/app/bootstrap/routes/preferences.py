from fastapi import APIRouter

from app.api.routes.v1.preferences.setting import build_settings_router
from app.bootstrap.dependencies.identity import get_authenticated_identity
from app.bootstrap.dependencies.preferences import (
    create_setting_dependency,
    delete_setting_dependency,
    get_setting_dependency,
    get_settings_dependency,
    update_setting_dependency,
)


def build_preferences_api_router() -> APIRouter:
    return build_settings_router(
        get_settings_dependency,
        get_setting_dependency,
        create_setting_dependency,
        update_setting_dependency,
        delete_setting_dependency,
        get_authenticated_identity,
    )
