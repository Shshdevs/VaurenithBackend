from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.identity.entities.client_device import ClientDevice
from app.domain.identity.enums import ClientDeviceStatus, PlatformType
from app.domain.identity.exceptions import InvalidClientDevice


def make_device() -> ClientDevice:
    return ClientDevice(
        entity_id=uuid4(),
        user_id=uuid4(),
        name="  Work laptop  ",
        platform=PlatformType.MACOS,
        registered_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_new_device_is_active_and_normalizes_its_name() -> None:
    device = make_device()

    assert device.is_active
    assert device.status is ClientDeviceStatus.ACTIVE
    assert device.name == "Work laptop"


def test_device_can_be_deactivated_and_activated() -> None:
    device = make_device()

    device.deactivate()
    assert device.status is ClientDeviceStatus.INACTIVE

    device.activate()
    assert device.status is ClientDeviceStatus.ACTIVE


def test_reactivation_does_not_change_terminal_revocation() -> None:
    device = make_device()
    device.deactivate()
    device.revoke(device.registered_at + timedelta(minutes=1))

    with pytest.raises(InvalidClientDevice):
        device.activate()
    assert device.status is ClientDeviceStatus.REVOKED


def test_device_metadata_can_be_updated_and_app_version_cleared() -> None:
    device = make_device()
    device.update_metadata(" New name ", "1.2.3", True)
    device.update_metadata(None, None, True)

    assert device.name == "New name"
    assert device.app_version is None


def test_revoked_device_cannot_be_reactivated() -> None:
    device = make_device()
    revoked_at = device.registered_at + timedelta(minutes=5)

    device.revoke(revoked_at)

    assert not device.is_active
    assert device.status is ClientDeviceStatus.REVOKED
    assert device.revoked_at == revoked_at
    with pytest.raises(InvalidClientDevice):
        device.activate()


def test_mark_seen_updates_last_seen_time() -> None:
    device = make_device()
    last_seen_at = device.registered_at + timedelta(minutes=5)

    device.mark_seen(last_seen_at)

    assert device.last_seen_at == last_seen_at


def test_last_seen_time_cannot_move_backwards() -> None:
    device = make_device()
    last_seen_at = device.registered_at + timedelta(minutes=5)
    device.mark_seen(last_seen_at)

    with pytest.raises(InvalidClientDevice):
        device.mark_seen(last_seen_at - timedelta(seconds=1))


def test_device_status_and_revocation_timestamp_must_match() -> None:
    registered_at = datetime(2026, 1, 1, tzinfo=UTC)

    with pytest.raises(InvalidClientDevice):
        ClientDevice(
            entity_id=uuid4(),
            user_id=uuid4(),
            name="Work laptop",
            platform=PlatformType.MACOS,
            registered_at=registered_at,
            status=ClientDeviceStatus.REVOKED,
        )
