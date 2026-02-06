from __future__ import annotations

import pytest

from parc_ferme.errors import GitHubError, PRNotFoundError
from parc_ferme.github import _validate_pr_input, _validate_repo


# --- _validate_pr_input ---


def test_validate_pr_number_valid():
    _validate_pr_input("123")  # should not raise


def test_validate_pr_url_valid():
    _validate_pr_input("https://github.com/owner/repo/pull/456")


def test_validate_pr_url_with_dots_hyphens():
    _validate_pr_input("https://github.com/my-org/my.repo/pull/1")


def test_validate_empty_string_raises():
    with pytest.raises(PRNotFoundError, match="Invalid PR reference"):
        _validate_pr_input("")


def test_validate_random_text_raises():
    with pytest.raises(PRNotFoundError):
        _validate_pr_input("hello")


def test_validate_partial_url_raises():
    with pytest.raises(PRNotFoundError):
        _validate_pr_input("github.com/owner/repo/pull/1")


def test_validate_url_with_trailing_slash_raises():
    with pytest.raises(PRNotFoundError):
        _validate_pr_input("https://github.com/owner/repo/pull/1/")


def test_validate_negative_number_raises():
    with pytest.raises(PRNotFoundError):
        _validate_pr_input("-1")


# --- _validate_repo ---


def test_validate_repo_valid():
    _validate_repo("owner/repo")  # should not raise


def test_validate_repo_with_dots_hyphens():
    _validate_repo("my-org/my.repo")  # should not raise


def test_validate_repo_empty_raises():
    with pytest.raises(GitHubError, match="Invalid repository format"):
        _validate_repo("")


def test_validate_repo_no_slash_raises():
    with pytest.raises(GitHubError):
        _validate_repo("justrepo")


def test_validate_repo_too_many_slashes_raises():
    with pytest.raises(GitHubError):
        _validate_repo("a/b/c")


def test_validate_repo_flag_injection_raises():
    with pytest.raises(GitHubError):
        _validate_repo("--flag")


def test_validate_repo_spaces_raises():
    with pytest.raises(GitHubError):
        _validate_repo("owner/repo name")
