from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from parc_ferme.config import _build_custom_profiles, load_config
from parc_ferme.errors import ConfigError

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# --- load_config ---


def test_load_explicit_valid_config():
    config = load_config(str(FIXTURES_DIR / "valid_config.yml"))
    assert config["default_profile"] == "security"
    assert config["claude_model"] == "sonnet"
    assert config["comment"]["enabled"] is True
    assert config["comment"]["mode"] == "update"
    assert "myprofile" in config["custom_profiles"]
    profile = config["custom_profiles"]["myprofile"]
    assert profile.system_role == "test reviewer"


def test_load_explicit_missing_file_raises():
    with pytest.raises(ConfigError, match="Config file not found"):
        load_config("/nonexistent/path/config.yml")


def test_load_invalid_yaml_raises():
    with pytest.raises(ConfigError, match="Config file must be a YAML mapping"):
        load_config(str(FIXTURES_DIR / "invalid_config.yml"))


def test_load_default_returns_defaults_when_no_files():
    with patch(
        "parc_ferme.config._discover_config_files", return_value=[]
    ):
        config = load_config()
    assert config["default_profile"] == "default"
    assert config["claude_model"] is None
    assert config["review_timeout"] == 300
    assert config["comment"]["enabled"] is False
    assert config["custom_profiles"] is None


def test_load_extends_config():
    config = load_config(str(FIXTURES_DIR / "extends_config.yml"))
    profiles = config["custom_profiles"]
    assert "extended-default" in profiles
    assert "docstrings" in profiles["extended-default"].extra_instructions


# --- _build_custom_profiles ---


def test_build_fully_custom_profile():
    raw = {
        "myprofile": {
            "description": "My profile",
            "system_role": "reviewer",
            "rules": ["rule1"],
            "checks": ["check1"],
        }
    }
    profiles = _build_custom_profiles(raw)
    assert "myprofile" in profiles
    assert profiles["myprofile"].rules == ["rule1"]


def test_build_extends_builtin():
    raw = {
        "ext": {
            "extends": "default",
            "extra_instructions": "Extra stuff",
        }
    }
    profiles = _build_custom_profiles(raw)
    assert "ext" in profiles
    assert "Extra stuff" in profiles["ext"].extra_instructions
    # Should inherit default's system_role
    assert profiles["ext"].system_role == "senior code reviewer"


def test_build_circular_extends_raises():
    raw = {
        "alpha": {"extends": "beta", "description": "alpha"},
        "beta": {"extends": "alpha", "description": "beta"},
    }
    with pytest.raises(ConfigError, match="Could not resolve"):
        _build_custom_profiles(raw)


def test_build_extends_chain():
    raw = {
        "level2": {
            "extends": "level1",
            "extra_instructions": "Level 2 instructions",
        },
        "level1": {
            "extends": "default",
            "extra_instructions": "Level 1 instructions",
        },
    }
    profiles = _build_custom_profiles(raw)
    assert "level1" in profiles
    assert "level2" in profiles
    assert "Level 1 instructions" in profiles["level2"].extra_instructions
    assert "Level 2 instructions" in profiles["level2"].extra_instructions


# --- review_timeout ---


def test_load_config_review_timeout():
    config = load_config(str(FIXTURES_DIR / "timeout_config.yml"))
    assert config["review_timeout"] == 600


def test_load_config_default_timeout():
    with patch(
        "parc_ferme.config._discover_config_files", return_value=[]
    ):
        config = load_config()
    assert config["review_timeout"] == 300


def test_load_config_invalid_timeout_raises():
    with pytest.raises(ConfigError, match="Invalid review_timeout"):
        load_config(str(FIXTURES_DIR / "invalid_timeout_config.yml"))
