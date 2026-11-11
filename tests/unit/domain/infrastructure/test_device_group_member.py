from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.infrastructure import DeviceGroupMember, InvalidDeviceGroupMember


def test_device_group_member_stores_association() -> None:
    membership_id, group_id, device_id = uuid4(), uuid4(), uuid4()
    created_at = datetime.now(UTC)

    member = DeviceGroupMember(membership_id, group_id, device_id, created_at)

    assert member.id == membership_id
    assert member.group_id == group_id
    assert member.device_id == device_id
    assert member.created_at == created_at


@pytest.mark.parametrize(
    ("membership_id", "group_id", "device_id", "created_at"),
    [
        ("invalid", uuid4(), uuid4(), datetime.now(UTC)),
        (uuid4(), "invalid", uuid4(), datetime.now(UTC)),
        (uuid4(), uuid4(), "invalid", datetime.now(UTC)),
        (uuid4(), uuid4(), uuid4(), datetime.now()),
    ],
)
def test_device_group_member_rejects_invalid_data(
    membership_id, group_id, device_id, created_at
) -> None:
    with pytest.raises(InvalidDeviceGroupMember):
        DeviceGroupMember(membership_id, group_id, device_id, created_at)
