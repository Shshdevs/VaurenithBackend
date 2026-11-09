from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest

from app.domain.infrastructure import (
    Container,
    ContainerImage,
    ContainerName,
    ContainerRuntimeId,
    Database,
    DatabaseCatalogName,
    DatabaseEndpoint,
    DatabaseResourceName,
    InvalidContainer,
    InvalidDatabase,
)
from app.domain.infrastructure.enums import ContainerStatus, DbmsType


def test_container_requires_value_objects_in_constructor() -> None:
    now = datetime.now(UTC)
    container = Container(
        entity_id=uuid4(),
        device_id=uuid4(),
        container_runtime_id=ContainerRuntimeId("docker:abc123"),
        name=ContainerName("api"),
        image=ContainerImage("example/api:1.0"),
        created_at=now,
        updated_at=now,
        status=ContainerStatus.RUNNING,
    )

    assert container.container_runtime_id == "docker:abc123"
    assert container.name == "api"
    assert container.image == "example/api:1.0"

    with pytest.raises(InvalidContainer):
        Container(
            entity_id=uuid4(),
            device_id=uuid4(),
            container_runtime_id=cast(Any, "docker:abc123"),
            name=ContainerName("api"),
            created_at=now,
            updated_at=now,
        )


def test_database_requires_value_objects_in_constructor() -> None:
    now = datetime.now(UTC)
    database = Database(
        entity_id=uuid4(),
        device_id=uuid4(),
        name=DatabaseResourceName("orders"),
        dbms_type=DbmsType.POSTGRESQL,
        endpoint=DatabaseEndpoint(host=" db.internal ", port=5432),
        database_name=DatabaseCatalogName("orders_prod"),
        created_at=now,
        updated_at=now,
    )

    assert database.name == "orders"
    assert database.host == "db.internal"
    assert database.port == 5432
    assert database.database_name == "orders_prod"

    with pytest.raises(InvalidDatabase):
        Database(
            entity_id=uuid4(),
            device_id=uuid4(),
            name=cast(Any, "orders"),
            dbms_type=DbmsType.POSTGRESQL,
            created_at=now,
            updated_at=now,
        )
