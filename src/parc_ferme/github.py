from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass

from .errors import GitHubError, PRNotFoundError, ToolNotFoundError

_GH_TIMEOUT = 30  # seconds

_PR_NUMBER_RE = re.compile(r"^\d+$")
_PR_URL_RE = re.compile(r"^https://github\.com/[\w.\-]+/[\w.\-]+/pull/\d+$")
_REPO_FORMAT_RE = re.compile(r"^[\w.\-]+/[\w.\-]+$")


def _validate_pr_input(pr_input: str) -> None:
    """Validate that pr_input is a PR number or GitHub PR URL."""
    if not (_PR_NUMBER_RE.match(pr_input) or _PR_URL_RE.match(pr_input)):
        raise PRNotFoundError(
            f"Invalid PR reference: '{pr_input}'. "
            "Expected a PR number (e.g. 123) or GitHub URL "
            "(e.g. https://github.com/owner/repo/pull/123)."
        )


def _validate_repo(repo: str) -> None:
    """Validate OWNER/REPO format."""
    if not _REPO_FORMAT_RE.match(repo):
        raise GitHubError(
            f"Invalid repository format: '{repo}'. "
            "Expected OWNER/REPO (e.g. 'owner/my-repo')."
        )


def _add_repo_flag(cmd: list[str], repo: str | None) -> None:
    if repo:
        _validate_repo(repo)
        cmd.extend(["-R", repo])


def _run_gh(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a gh CLI command with timeout."""
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=_GH_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise GitHubError(
            f"Timed out after {_GH_TIMEOUT}s waiting for: {' '.join(cmd[:4])}"
        )


@dataclass
class PRInfo:
    title: str
    number: int
    url: str
    author: str
    base_branch: str


def check_gh_available() -> None:
    if shutil.which("gh") is None:
        raise ToolNotFoundError(
            "'gh' CLI not found. Install it from https://cli.github.com/"
        )


def get_pr_info(pr_input: str, repo: str | None = None) -> PRInfo:
    _validate_pr_input(pr_input)
    cmd = [
        "gh", "pr", "view", pr_input,
        "--json", "title,number,url,author,baseRefName",
    ]
    _add_repo_flag(cmd, repo)

    result = _run_gh(cmd)
    if result.returncode != 0:
        raise PRNotFoundError(
            f"Could not find PR '{pr_input}': {result.stderr.strip()}"
        )

    data = json.loads(result.stdout)
    return PRInfo(
        title=data["title"],
        number=data["number"],
        url=data["url"],
        author=data["author"]["login"],
        base_branch=data["baseRefName"],
    )


def get_pr_diff(pr_input: str, repo: str | None = None) -> str:
    _validate_pr_input(pr_input)
    cmd = ["gh", "pr", "diff", pr_input]
    _add_repo_flag(cmd, repo)

    result = _run_gh(cmd)
    if result.returncode != 0:
        raise PRNotFoundError(
            f"Could not get diff for PR '{pr_input}': {result.stderr.strip()}"
        )
    return result.stdout


def get_changed_files(pr_input: str, repo: str | None = None) -> list[str]:
    _validate_pr_input(pr_input)
    cmd = ["gh", "pr", "diff", pr_input, "--name-only"]
    _add_repo_flag(cmd, repo)

    result = _run_gh(cmd)
    if result.returncode != 0:
        print(
            f"Warning: Could not list changed files: {result.stderr.strip()}",
            file=sys.stderr,
        )
        return []
    return [f for f in result.stdout.strip().split("\n") if f]


def post_comment(
    pr_input: str,
    body: str,
    repo: str | None = None,
    edit_last: bool = False,
) -> None:
    _validate_pr_input(pr_input)

    fd, body_path = tempfile.mkstemp(suffix=".md", prefix="parc-ferme-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(body)

        cmd = ["gh", "pr", "comment", pr_input, "--body-file", body_path]
        if edit_last:
            cmd.append("--edit-last")
        _add_repo_flag(cmd, repo)

        result = _run_gh(cmd)
        if result.returncode != 0:
            raise GitHubError(
                f"Failed to post comment: {result.stderr.strip()}"
            )
    finally:
        os.unlink(body_path)
