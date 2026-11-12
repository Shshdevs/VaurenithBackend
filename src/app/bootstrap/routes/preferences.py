from fastapi import APIRouter

from app.api.routes.v1.preferences import build_preferences_entity_router
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
    entity_router = build_settings_router(
        get_settings_dependency,
        get_setting_dependency,
        create_setting_dependency,
        update_setting_dependency,
        delete_setting_dependency,
        get_authenticated_identity,
    )
    router = APIRouter()
    router.include_router(build_preferences_entity_router([entity_router]))
    return router
