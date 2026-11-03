from decimal import Decimal
from typing import cast

import pytest

from app.domain.development.exceptions import (
    InvalidBranch,
    InvalidCodeComponent,
    InvalidCommitHash,
    InvalidDependency,
)
from app.domain.development.value_objects import (
    BranchName,
    CommitHash,
    ComponentName,
    ComponentPath,
    Confidence,
    DefaultBranchName,
    RemoteRepositoryUrl,
    RepositoryName,
)


def test_branch_name_and_default_branch_name_share_one_value_type() -> None:
    branch_name = BranchName("main")
    default_branch_name = DefaultBranchName("main")

    assert type(default_branch_name) is BranchName
    assert branch_name == default_branch_name


@pytest.mark.parametrize("value", ["", "feature name", "feature..name", "-name"])
def test_branch_name_rejects_invalid_git_refs(value: str) -> None:
    with pytest.raises(InvalidBranch):
        BranchName(value)


def test_commit_hash_accepts_sha1_and_sha256() -> None:
    assert CommitHash("a" * 40).value == "a" * 40
    assert CommitHash("B" * 64).value == "b" * 64


def test_commit_hash_rejects_non_hexadecimal_values() -> None:
    with pytest.raises(InvalidCommitHash):
        CommitHash("g" * 40)


def test_confidence_normalizes_values_representable_by_numeric_scale() -> None:
    confidence = Confidence(Decimal("0.12500"))

    assert confidence.value == Decimal("0.1250")


def test_component_name_and_path_reject_blank_values() -> None:
    with pytest.raises(InvalidCodeComponent):
        ComponentName("  ")
    with pytest.raises(InvalidCodeComponent):
        ComponentPath("  ")


def test_repository_values_trim_outer_whitespace() -> None:
    assert RepositoryName("  project  ").value == "project"
    assert RemoteRepositoryUrl(" git@host:project.git ").value == "git@host:project.git"


def test_default_branch_name_alias_uses_branch_validation() -> None:
    with pytest.raises(InvalidBranch):
        DefaultBranchName("invalid branch")


def test_confidence_rejects_non_decimal_values() -> None:
    with pytest.raises(InvalidDependency):
        Confidence(cast(Decimal, 0.5))
