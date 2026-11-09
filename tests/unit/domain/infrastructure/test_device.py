from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.domain.infrastructure import (
    Device,
    DeviceName,
    InvalidDevice,
    OperatingSystem,
)
from app.domain.infrastructure.enums import DeviceType


def make_device(**overrides: Any) -> Device:
    now = datetime.now(UTC)
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "user_id": uuid4(),
        "name": DeviceName("worker-01"),
        "created_at": now,
        "updated_at": now,
        "device_type": DeviceType.VPS,
        "operating_system_info": OperatingSystem("Linux", "6.1", "x86_64"),
        "tags": ["production"],
    }
    values.update(overrides)
    return Device(**values)


def test_device_keeps_value_objects_and_returns_defensive_tags_copy() -> None:
    device = make_device(name=DeviceName("  node-01  "))
    tags = device.tags
    assert device.name == "node-01"
    assert device.name_value == DeviceName("node-01")
    assert device.operating_system_info == OperatingSystem("Linux", "6.1", "x86_64")
    assert tags == ["production"]
    assert tags is not None
    tags.append("mutated")
    assert device.tags == ["production"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entity_id", "not-a-uuid"),
        ("user_id", "not-a-uuid"),
        ("name", "worker-01"),
        ("device_type", "vps"),
        ("version", True),
        ("tags", ["production", "  "]),
        ("created_at", datetime(2026, 1, 1)),
    ],
)
def test_device_rejects_invalid_fields(field: str, value: object) -> None:
    with pytest.raises(InvalidDevice):
        make_device(**{field: value})


def test_device_rejects_invalid_timestamps() -> None:
    now = datetime.now(UTC)
    with pytest.raises(InvalidDevice):
        make_device(updated_at=now - timedelta(seconds=1), created_at=now)


@pytest.mark.parametrize("name", ["  ", "x" * 256])
def test_device_name_rejects_invalid_values(name: str) -> None:
    with pytest.raises(InvalidDevice):
        DeviceName(name)


def test_operating_system_normalizes_and_validates_its_fields() -> None:
    operating_system = OperatingSystem(" Linux ", " 6.1 ", None)
    assert operating_system.name == "Linux"
    assert operating_system.version == "6.1"
    with pytest.raises(InvalidDevice):
        OperatingSystem(None, "  ", None)
    with pytest.raises(InvalidDevice):
        OperatingSystem("x" * 101, None, None)
