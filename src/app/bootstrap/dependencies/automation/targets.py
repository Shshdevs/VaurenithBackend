from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.automation import AddScriptTarget, GetScriptTargets, RemoveScriptTarget
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.automation import (
    provide_add_script_target,
    provide_get_script_targets,
    provide_remove_script_target,
)


def add_automation_script_target_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> AddScriptTarget:
    return provide_add_script_target(session)


def get_automation_script_targets_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetScriptTargets:
    return provide_get_script_targets(session)


def remove_automation_script_target_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> RemoveScriptTarget:
    return provide_remove_script_target(session)
