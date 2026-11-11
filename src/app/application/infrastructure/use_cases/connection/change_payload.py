from app.domain.infrastructure import Connection


def connection_change_payload(connection: Connection) -> dict[str, object]:
    return {
        "device_id": str(connection.device_id),
        "name": connection.name,
        "slug": connection.slug,
        "host": connection.host,
        "port": connection.port,
        "username": connection.username,
        "authentication_type": connection.authentication_type.value,
        "connection_timeout": connection.connection_timeout,
        "is_default": connection.is_default,
        "last_connected_at": connection.last_connected_at.isoformat()
        if connection.last_connected_at is not None
        else None,
        "last_status": connection.last_status.value,
    }
