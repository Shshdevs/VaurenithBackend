from typing import Any

from app.domain.infrastructure import Database


def database_change_payload(database: Database) -> dict[str, Any]:
    return {
        "device_id": str(database.device_id),
        "project_id": str(database.project_id) if database.project_id is not None else None,
        "environment_id": str(database.environment_id)
        if database.environment_id is not None
        else None,
        "container_id": str(database.container_id)
        if database.container_id is not None
        else None,
        "service_id": str(database.service_id) if database.service_id is not None else None,
        "name": database.name,
        "dbms_type": database.dbms_type.value,
        "host": database.host,
        "port": database.port,
        "database_name": database.database_name,
        "status": database.status.value,
        "last_checked_at": database.last_checked_at.isoformat()
        if database.last_checked_at is not None
        else None,
    }
