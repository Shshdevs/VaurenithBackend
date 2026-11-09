from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.domain.infrastructure import DeviceGroup, DeviceGroupName, InvalidDeviceGroup


def make_device_group(**overrides: Any) -> DeviceGroup:
    now = datetime.now(UTC)
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "user_id": uuid4(),
        "name": DeviceGroupName("Production servers"),
        "created_at": now,
        "updated_at": now,
        "description": "Production infrastructure",
    }
    values.update(overrides)
    return DeviceGroup(**values)


def test_device_group_normalizes_name_and_description_and_generates_slug() -> None:
    group = make_device_group(
        name=DeviceGroupName("  Production Servers  "),
        description="  Primary fleet  ",
    )

    assert group.name == "Production Servers"
    assert group.name_value == DeviceGroupName("Production Servers")
    assert group.description == "Primary fleet"
    assert group.slug == "production-servers"


def test_device_group_accepts_empty_description_as_none() -> None:
    group = make_device_group(description="  ")

    assert group.description is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entity_id", "not-a-uuid"),
        ("user_id", "not-a-uuid"),
        ("name", "Production servers"),
        ("description", 42),
        ("created_at", datetime(2026, 1, 1)),
        ("updated_at", datetime(2026, 1, 1)),
    ],
)
def test_device_group_rejects_invalid_fields(field: str, value: object) -> None:
    with pytest.raises(InvalidDeviceGroup):
        make_device_group(**{field: value})


def test_device_group_rejects_update_time_before_creation() -> None:
    now = datetime.now(UTC)

    with pytest.raises(InvalidDeviceGroup):
        make_device_group(
            created_at=now,
            updated_at=now - timedelta(seconds=1),
        )


def test_device_group_name_rejects_non_string_values() -> None:
    with pytest.raises(InvalidDeviceGroup):
        DeviceGroupName(42)


@pytest.mark.parametrize("name", ["  ", "x" * 256])
def test_device_group_name_rejects_invalid_values(name: str) -> None:
    with pytest.raises(InvalidDeviceGroup):
        DeviceGroupName(name)
