from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError
from .profiles import (
    BUILTIN_PROFILES,
    DEFAULT_SEVERITY_LEVELS,
    Profile,
    merge_profile,
    parse_severity_levels,
)

CONFIG_FILENAME = ".reviewrc.yml"
USER_CONFIG_DIR = Path.home() / ".config" / "parc-ferme"


def _find_git_root() -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _discover_config_files() -> list[Path]:
    """Find config files in order of precedence (lowest first)."""
    paths: list[Path] = []

    # User-level config
    user_config = USER_CONFIG_DIR / CONFIG_FILENAME
    if user_config.exists():
        paths.append(user_config)

    # Project-level config (git root or cwd)
    git_root = _find_git_root()
    search_dir = git_root or Path.cwd()
    project_config = search_dir / CONFIG_FILENAME
    if project_config.exists():
        paths.append(project_config)

    return paths


def _parse_yaml(path: Path) -> dict[str, Any]:
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ConfigError(f"Config file must be a YAML mapping: {path}")
        return data
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}")


def _build_custom_profiles(raw_profiles: dict[str, Any]) -> dict[str, Profile]:
    """Build Profile objects from config, supporting 'extends' keyword.

    Uses multi-pass resolution to handle custom profiles extending other
    custom profiles regardless of declaration order in YAML.
    """
    custom: dict[str, Profile] = {}
    unresolved = dict(raw_profiles)

    max_passes = len(unresolved) + 1
    for _ in range(max_passes):
        if not unresolved:
            break
        still_unresolved: dict[str, Any] = {}
        for name, definition in unresolved.items():
            if not isinstance(definition, dict):
                continue

            extends = definition.get("extends")
            if extends:
                base = BUILTIN_PROFILES.get(extends) or custom.get(extends)
                if base is None:
                    still_unresolved[name] = definition
                    continue
                profile = merge_profile(base, {**definition, "name": name})
            else:
                # Fully custom profile
                try:
                    raw_levels = definition.get("severity_levels")
                    severity_levels = (
                        parse_severity_levels(raw_levels)
                        if raw_levels and isinstance(raw_levels, list)
                        else DEFAULT_SEVERITY_LEVELS
                    )
                    profile = Profile(
                        name=name,
                        description=definition.get("description", name),
                        system_role=definition.get("system_role", "code reviewer"),
                        rules=definition.get("rules", []),
                        checks=definition.get("checks", []),
                        severity_levels=severity_levels,
                        output_format=definition.get(
                            "output_format", "[SEVERITY] file:line — description"
                        ),
                        extra_instructions=definition.get("extra_instructions", ""),
                    )
                except (TypeError, KeyError) as e:
                    raise ConfigError(f"Invalid profile '{name}': {e}")

            custom[name] = profile
        unresolved = still_unresolved
    else:
        names = ", ".join(sorted(unresolved.keys()))
        raise ConfigError(
            f"Could not resolve profiles (circular or missing extends?): {names}"
        )

    return custom


def load_config(explicit_path: str | None = None) -> dict[str, Any]:
    """Load and merge configuration from all sources.

    Returns a dict with keys:
        - default_profile: str
        - claude_model: str | None
        - review_timeout: int
        - comment: dict (enabled, mode)
        - custom_profiles: dict[str, Profile] | None
    """
    merged: dict[str, Any] = {
        "default_profile": "default",
        "claude_model": None,
        "review_timeout": 300,
        "comment": {"enabled": False, "mode": "create"},
        "custom_profiles": None,
    }

    # Determine config files to load
    if explicit_path:
        path = Path(explicit_path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {explicit_path}")
        config_files = [path]
    else:
        config_files = _discover_config_files()

    # Merge all config files
    all_raw_profiles: dict[str, Any] = {}

    for config_file in config_files:
        data = _parse_yaml(config_file)

        if "default_profile" in data:
            merged["default_profile"] = data["default_profile"]
        if "claude_model" in data:
            merged["claude_model"] = data["claude_model"]
        if "review_timeout" in data:
            try:
                merged["review_timeout"] = int(data["review_timeout"])
            except (ValueError, TypeError):
                raise ConfigError(
                    f"Invalid review_timeout value: '{data['review_timeout']}' "
                    "(must be an integer)"
                )
        if "comment" in data and isinstance(data["comment"], dict):
            merged["comment"].update(data["comment"])
        if "profiles" in data and isinstance(data["profiles"], dict):
            all_raw_profiles.update(data["profiles"])

    # Build custom profiles
    if all_raw_profiles:
        merged["custom_profiles"] = _build_custom_profiles(all_raw_profiles)

    return merged
