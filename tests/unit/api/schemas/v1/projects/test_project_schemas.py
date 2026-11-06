import pytest
from pydantic import ValidationError

from app.api.schemas.v1.projects.project import ProjectData
from app.api.schemas.v1.projects.project_create import ProjectCreateRequest
from app.domain.projects import ProjectStatus, ProjectType


def test_project_create_request_normalizes_name_and_applies_defaults() -> None:
    request = ProjectCreateRequest.model_validate({"name": "  Project gamma  "})

    assert request.name == "Project gamma"
    assert request.project_type is ProjectType.OTHER
    assert request.version == 1
    assert request.description is None
    assert request.metadata is None


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "   "},
        {"name": "x" * 256},
        {"name": "Project delta", "version": 0},
        {"name": "Project delta", "extra": "forbidden"},
    ],
)
def test_project_create_request_rejects_invalid_values(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        ProjectCreateRequest.model_validate(payload)


def test_project_data_accepts_application_dto_values() -> None:
    from datetime import UTC, datetime
    from uuid import uuid4

    timestamp = datetime.now(UTC)
    data = ProjectData.model_validate(
        {
            "id": uuid4(),
            "user_id": uuid4(),
            "name": "Project epsilon",
            "description": None,
            "project_type": ProjectType.SOFTWARE.value,
            "status": ProjectStatus.ACTIVE.value,
            "metadata": {"key": "value"},
            "version": 2,
            "created_at": timestamp,
            "updated_at": timestamp,
            "deleted_at": None,
        }
    )

    assert data.project_type is ProjectType.SOFTWARE
    assert data.status is ProjectStatus.ACTIVE
    assert data.metadata == {"key": "value"}
