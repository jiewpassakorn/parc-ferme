from __future__ import annotations

import pytest

from parc_ferme.github import PRInfo
from parc_ferme.profiles import DEFAULT_SEVERITY_LEVELS, Profile


@pytest.fixture
def sample_pr_info():
    return PRInfo(
        title="Fix login bug",
        number=42,
        url="https://github.com/owner/repo/pull/42",
        author="testuser",
        base_branch="main",
    )


@pytest.fixture
def sample_profile():
    return Profile(
        name="default",
        description="General code review",
        system_role="senior code reviewer",
        rules=["Only flag REAL issues"],
        checks=["Bugs: Logic errors"],
        severity_levels=DEFAULT_SEVERITY_LEVELS,
    )
