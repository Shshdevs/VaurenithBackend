from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.preferences import InvalidSetting, Setting, SettingScope


def make_setting(**overrides: object) -> Setting:
    values: dict[str, object] = {
        "entity_id": uuid4(),
        "user_id": uuid4(),
        "scope": SettingScope.GLOBAL,
        "key": "theme",
        "created_at": datetime(2025, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2025, 1, 1, tzinfo=UTC),
        "value": {"mode": "dark"},
    }
    values.update(overrides)
    return Setting(**values)  # type: ignore[arg-type]


def test_setting_keeps_fields_and_copies_json_value() -> None:
    original = {"nested": [1]}
    setting = make_setting(value=original)
    original["nested"].append(2)

    assert setting.id is not None
    assert setting.value == {"nested": [1]}
    returned = setting.value
    returned["nested"].append(3)
    assert setting.value == {"nested": [1]}


def test_client_scope_requires_device() -> None:
    with pytest.raises(InvalidSetting):
        make_setting(scope=SettingScope.CLIENT)


def test_global_scope_rejects_device() -> None:
    with pytest.raises(InvalidSetting):
        make_setting(client_device_id=uuid4())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entity_id", "invalid"),
        ("user_id", "invalid"),
        ("client_device_id", "invalid"),
        ("scope", "global"),
        ("key", "k" * 256),
        ("version", 0),
        ("version", 2**63),
        ("version", True),
        ("created_at", datetime(2025, 1, 1)),
        ("updated_at", datetime(2024, 12, 31, tzinfo=UTC)),
    ],
)
def test_setting_rejects_invalid_fields(field: str, value: object) -> None:
    with pytest.raises(InvalidSetting):
        make_setting(**{field: value})


def test_setting_accepts_client_scope_with_device_and_version() -> None:
    device_id = uuid4()
    setting = make_setting(
        scope=SettingScope.CLIENT,
        client_device_id=device_id,
        version=3,
        updated_at=datetime(2025, 1, 2, tzinfo=UTC),
    )

    assert setting.scope is SettingScope.CLIENT
    assert setting.client_device_id == device_id
    assert setting.version == 3


def test_setting_value_is_independent_of_input_copy() -> None:
    value = {"items": ["a"]}
    snapshot = {"items": ["a"]}
    setting = make_setting(value=value)
    assert setting.value == snapshot
