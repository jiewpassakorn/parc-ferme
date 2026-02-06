from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from parc_ferme.errors import ReviewError
from parc_ferme.profiles import DEFAULT_SEVERITY_LEVELS, Profile
from parc_ferme.reviewer import MAX_DIFF_CHARS, build_prompt, run_review


# --- build_prompt ---


def test_build_prompt_contains_pr_info(sample_pr_info, sample_profile):
    prompt = build_prompt(sample_pr_info, sample_profile)
    assert "#42" in prompt
    assert "Fix login bug" in prompt
    assert "testuser" in prompt
    assert "main" in prompt


def test_build_prompt_contains_rules(sample_pr_info, sample_profile):
    prompt = build_prompt(sample_pr_info, sample_profile)
    for rule in sample_profile.rules:
        assert rule in prompt


def test_build_prompt_contains_checks(sample_pr_info, sample_profile):
    prompt = build_prompt(sample_pr_info, sample_profile)
    for check in sample_profile.checks:
        assert check in prompt


def test_build_prompt_contains_severity_levels(sample_pr_info, sample_profile):
    prompt = build_prompt(sample_pr_info, sample_profile)
    for level in sample_profile.severity_levels:
        assert level.label in prompt
        assert level.description in prompt


def test_build_prompt_contains_output_format(sample_pr_info, sample_profile):
    prompt = build_prompt(sample_pr_info, sample_profile)
    assert sample_profile.output_format in prompt


def test_build_prompt_with_extra_instructions(sample_pr_info):
    profile = Profile(
        name="test",
        description="Test",
        system_role="reviewer",
        rules=["rule"],
        checks=["check"],
        severity_levels=DEFAULT_SEVERITY_LEVELS,
        extra_instructions="Pay attention to SQL injection",
    )
    prompt = build_prompt(sample_pr_info, profile)
    assert "Pay attention to SQL injection" in prompt


def test_build_prompt_without_extra_instructions(sample_pr_info, sample_profile):
    prompt = build_prompt(sample_pr_info, sample_profile)
    # Should not have trailing blank extra section
    lines = prompt.strip().split("\n")
    assert lines[-1] == sample_profile.output_format


# --- run_review ---


@patch("parc_ferme.reviewer.subprocess.run")
def test_run_review_short_diff_no_truncation(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="LGTM", stderr="")
    result = run_review("prompt", "short diff")
    assert result == "LGTM"
    # Check the diff passed to stdin
    call_kwargs = mock_run.call_args
    assert "DIFF TRUNCATED" not in call_kwargs.kwargs.get("input", call_kwargs[1].get("input", ""))


@patch("parc_ferme.reviewer.subprocess.run")
def test_run_review_long_diff_truncated(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="review", stderr="")
    long_diff = "x" * (MAX_DIFF_CHARS + 1000)
    run_review("prompt", long_diff)
    call_kwargs = mock_run.call_args
    input_text = call_kwargs.kwargs.get("input") or call_kwargs[1].get("input", "")
    assert "DIFF TRUNCATED" in input_text
    assert len(input_text) < len(long_diff)


@patch("parc_ferme.reviewer.subprocess.run")
def test_run_review_failure_raises(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
    with pytest.raises(ReviewError, match="Claude review failed"):
        run_review("prompt", "diff")


@patch("parc_ferme.reviewer.subprocess.run")
def test_run_review_passes_model_flag(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
    run_review("prompt", "diff", model="opus")
    cmd = mock_run.call_args[0][0]
    assert "--model" in cmd
    assert "opus" in cmd


@patch("parc_ferme.reviewer.subprocess.run")
def test_run_review_no_model_flag(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
    run_review("prompt", "diff", model=None)
    cmd = mock_run.call_args[0][0]
    assert "--model" not in cmd


@patch("parc_ferme.reviewer.subprocess.run")
def test_run_review_timeout_raises(mock_run):
    import subprocess as sp
    mock_run.side_effect = sp.TimeoutExpired(cmd=["claude"], timeout=10)
    with pytest.raises(ReviewError, match="timed out after 10s"):
        run_review("prompt", "diff", timeout=10)
