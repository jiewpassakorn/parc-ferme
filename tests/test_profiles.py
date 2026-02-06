from __future__ import annotations

import pytest

from parc_ferme.profiles import (
    BUILTIN_PROFILES,
    DEFAULT_SEVERITY_LEVELS,
    Profile,
    SeverityLevel,
    get_profile,
    list_profiles,
    merge_profile,
    parse_severity_levels,
)


# --- get_profile ---


@pytest.mark.parametrize("name", ["default", "security", "performance", "angular"])
def test_get_builtin_profile(name):
    profile = get_profile(name)
    assert profile.name == name
    assert isinstance(profile, Profile)


def test_get_unknown_profile_raises():
    with pytest.raises(ValueError, match="Unknown profile 'nonexistent'"):
        get_profile("nonexistent")


def test_get_custom_profile():
    custom = Profile(
        name="custom",
        description="Custom",
        system_role="reviewer",
        rules=[],
        checks=[],
    )
    result = get_profile("custom", custom_profiles={"custom": custom})
    assert result is custom


def test_custom_overrides_builtin():
    override = Profile(
        name="default",
        description="Overridden default",
        system_role="override",
        rules=["rule1"],
        checks=["check1"],
    )
    result = get_profile("default", custom_profiles={"default": override})
    assert result.description == "Overridden default"


# --- list_profiles ---


def test_list_builtin_profiles():
    profiles = list_profiles()
    assert set(profiles.keys()) == {"default", "security", "performance", "angular"}


def test_list_with_custom_profiles():
    custom = Profile(
        name="extra",
        description="Extra",
        system_role="reviewer",
        rules=[],
        checks=[],
    )
    profiles = list_profiles(custom_profiles={"extra": custom})
    assert "extra" in profiles
    assert "default" in profiles


# --- parse_severity_levels ---


def test_parse_severity_levels_from_dicts():
    raw = [{"emoji": "X", "label": "Y", "description": "Z"}]
    result = parse_severity_levels(raw)
    assert len(result) == 1
    assert result[0] == SeverityLevel("X", "Y", "Z")


def test_parse_severity_levels_missing_keys():
    raw = [{"emoji": "!"}]
    result = parse_severity_levels(raw)
    assert result[0].label == ""
    assert result[0].description == ""


# --- merge_profile ---


def test_merge_overrides_description():
    base = BUILTIN_PROFILES["default"]
    merged = merge_profile(base, {"description": "New desc"})
    assert merged.description == "New desc"
    assert merged.system_role == base.system_role
    assert merged.rules == base.rules


def test_merge_appends_extra_instructions():
    base = Profile(
        name="base",
        description="Base",
        system_role="reviewer",
        rules=[],
        checks=[],
        extra_instructions="A",
    )
    merged = merge_profile(base, {"extra_instructions": "B"})
    assert merged.extra_instructions == "A\nB"


def test_merge_replaces_rules():
    base = BUILTIN_PROFILES["default"]
    new_rules = ["New rule 1", "New rule 2"]
    merged = merge_profile(base, {"rules": new_rules})
    assert merged.rules == new_rules


def test_merge_severity_levels_from_dicts():
    base = BUILTIN_PROFILES["default"]
    raw_levels = [{"emoji": "!", "label": "HIGH", "description": "High priority"}]
    merged = merge_profile(base, {"severity_levels": raw_levels})
    assert len(merged.severity_levels) == 1
    assert merged.severity_levels[0].label == "HIGH"


def test_merge_severity_levels_from_objects():
    base = BUILTIN_PROFILES["default"]
    levels = [SeverityLevel("!", "HIGH", "High priority")]
    merged = merge_profile(base, {"severity_levels": levels})
    assert merged.severity_levels == levels


def test_merge_no_severity_override_keeps_base():
    base = BUILTIN_PROFILES["default"]
    merged = merge_profile(base, {"description": "No change to severity"})
    assert merged.severity_levels == base.severity_levels
