from __future__ import annotations

import pytest

from parc_ferme.cli import _has_critical_issues, _print_err, parse_args


def test_parse_args_pr_number():
    args = parse_args(["123"])
    assert args.pr == "123"
    assert args.profile is None
    assert args.comment is False
    assert args.dry_run is False
    assert args.verbose is False


def test_parse_args_pr_url():
    args = parse_args(["https://github.com/o/r/pull/1"])
    assert args.pr == "https://github.com/o/r/pull/1"


def test_parse_args_profile_short():
    args = parse_args(["123", "-p", "security"])
    assert args.profile == "security"


def test_parse_args_profile_long():
    args = parse_args(["123", "--profile", "security"])
    assert args.profile == "security"


def test_parse_args_comment_flag():
    args = parse_args(["123", "-c"])
    assert args.comment is True


def test_parse_args_comment_mode():
    args = parse_args(["123", "--comment-mode", "update"])
    assert args.comment_mode == "update"


def test_parse_args_repo():
    args = parse_args(["123", "-R", "owner/repo"])
    assert args.repo == "owner/repo"


def test_parse_args_config():
    args = parse_args(["123", "--config", "/path/to/config"])
    assert args.config == "/path/to/config"


def test_parse_args_dry_run():
    args = parse_args(["123", "--dry-run"])
    assert args.dry_run is True


def test_parse_args_list_profiles():
    args = parse_args(["--list-profiles"])
    assert args.list_profiles is True
    assert args.pr is None


def test_parse_args_no_color():
    args = parse_args(["123", "--no-color"])
    assert args.no_color is True


def test_parse_args_verbose():
    args = parse_args(["123", "-v"])
    assert args.verbose is True


def test_parse_args_no_pr():
    args = parse_args([])
    assert args.pr is None


def test_parse_args_version():
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--version"])
    assert exc_info.value.code == 0


# --- New flags ---


def test_parse_args_output_short():
    args = parse_args(["123", "-o", "review.md"])
    assert args.output == "review.md"


def test_parse_args_output_long():
    args = parse_args(["123", "--output", "review.md"])
    assert args.output == "review.md"


def test_parse_args_timeout():
    args = parse_args(["123", "--timeout", "600"])
    assert args.timeout == 600


def test_parse_args_strict():
    args = parse_args(["123", "--strict"])
    assert args.strict is True


# --- _has_critical_issues ---


def test_has_critical_issues_found():
    assert _has_critical_issues("\U0001f534 CRITICAL - file.py:10 — bug") is True


def test_has_critical_issues_not_found():
    assert _has_critical_issues("\U0001f7e1 WARNING - file.py:10 — minor") is False


def test_has_critical_issues_lgtm():
    assert _has_critical_issues("\u2705 LGTM") is False


def test_has_critical_issues_case_sensitive():
    assert _has_critical_issues("critical") is False


# --- _print_err ---


def test_print_err_no_color(capsys):
    _print_err("test error", no_color=True)
    captured = capsys.readouterr()
    assert "\033[" not in captured.err
    assert "Error: test error" in captured.err


def test_print_err_with_color(capsys):
    _print_err("test error", no_color=False)
    captured = capsys.readouterr()
    assert "\033[0;31m" in captured.err
