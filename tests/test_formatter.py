from __future__ import annotations

from unittest.mock import patch

import pytest

from parc_ferme.formatter import (
    _escape_md,
    format_changed_files,
    format_comment,
    format_header,
    format_review_end,
    format_review_start,
)


# --- _escape_md ---


def test_escape_md_special_chars():
    result = _escape_md("Hello *world* [link](url)")
    assert "\\*" in result
    assert "\\[" in result
    assert "\\(" in result


def test_escape_md_no_special_chars():
    assert _escape_md("plain text 123") == "plain text 123"


def test_escape_md_all_specials():
    for ch in r"\`*_{}[]()#+-.!|<>":
        result = _escape_md(ch)
        assert result == f"\\{ch}", f"Failed to escape '{ch}'"


# --- format_header ---


def test_format_header_contains_pr_info(sample_pr_info):
    output = format_header(sample_pr_info)
    assert "#42" in output
    assert "Fix login bug" in output
    assert "testuser" in output
    assert "main" in output
    assert sample_pr_info.url in output


def test_format_header_no_color(sample_pr_info):
    output = format_header(sample_pr_info, no_color=True)
    assert "\033[" not in output


def test_format_header_with_color(sample_pr_info):
    output = format_header(sample_pr_info, no_color=False)
    assert "\033[" in output


# --- format_changed_files ---


def test_format_changed_files_lists_files():
    output = format_changed_files(["a.py", "b.py"])
    assert "a.py" in output
    assert "b.py" in output


def test_format_changed_files_no_color():
    output = format_changed_files(["a.py"], no_color=True)
    assert "\033[" not in output


def test_format_changed_files_empty_returns_empty_string():
    assert format_changed_files([]) == ""


# --- format_review_start / format_review_end ---


def test_format_review_start_no_color():
    output = format_review_start(no_color=True)
    assert "\033[" not in output
    assert "Claude Review" in output


def test_format_review_end_no_color():
    output = format_review_end(no_color=True)
    assert "\033[" not in output
    assert "Review complete" in output


# --- format_comment ---


def test_format_comment_contains_pr_number_and_title(sample_pr_info):
    output = format_comment(sample_pr_info, "LGTM", "default")
    assert "#42" in output
    assert "Fix login bug" in output


def test_format_comment_contains_profile_name(sample_pr_info):
    output = format_comment(sample_pr_info, "LGTM", "security")
    assert "security" in output


def test_format_comment_contains_review_body(sample_pr_info):
    output = format_comment(sample_pr_info, "Found 3 issues", "default")
    assert "Found 3 issues" in output


def test_format_comment_escapes_title():
    from parc_ferme.github import PRInfo

    pr = PRInfo(
        title="Fix *critical* bug",
        number=1,
        url="https://github.com/o/r/pull/1",
        author="user",
        base_branch="main",
    )
    output = format_comment(pr, "LGTM", "default")
    assert "\\*critical\\*" in output
