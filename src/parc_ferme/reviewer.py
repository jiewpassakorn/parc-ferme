from __future__ import annotations

import shutil
import subprocess

from .errors import ReviewError, ToolNotFoundError
from .github import PRInfo
from .profiles import Profile

MAX_DIFF_CHARS = 100_000  # ~100KB

_TRUNCATION_NOTICE = (
    "\n\n... [DIFF TRUNCATED: exceeded {limit:,} characters. "
    "Review covers the first {limit:,} characters only.] ...\n"
)


def check_claude_available() -> None:
    if shutil.which("claude") is None:
        raise ToolNotFoundError(
            "'claude' CLI not found. Install Claude Code first."
        )


def build_prompt(pr_info: PRInfo, profile: Profile) -> str:
    lines = [
        f"You are a {profile.system_role}. Review this PR diff.",
        "",
        f"PR: #{pr_info.number} - {pr_info.title}",
        f"Author: {pr_info.author}",
        f"Base branch: {pr_info.base_branch}",
        "",
        "RULES:",
    ]
    for rule in profile.rules:
        lines.append(f"- {rule}")

    lines.append("")
    lines.append("CHECK FOR:")
    for check in profile.checks:
        lines.append(f"- {check}")

    lines.append("")
    lines.append("SEVERITY LEVELS:")
    for level in profile.severity_levels:
        lines.append(f"{level.emoji} {level.label} - {level.description}")

    lines.append("")
    lines.append(f"FORMAT each issue as:\n{profile.output_format}")

    if profile.extra_instructions:
        lines.append("")
        lines.append(profile.extra_instructions)

    return "\n".join(lines)


def run_review(
    prompt: str,
    diff: str,
    model: str | None = None,
    timeout: int = 300,
    max_diff_chars: int = MAX_DIFF_CHARS,
) -> str:
    if len(diff) > max_diff_chars:
        diff = diff[:max_diff_chars] + _TRUNCATION_NOTICE.format(limit=max_diff_chars)

    cmd = ["claude", "-p", prompt]
    if model:
        cmd.extend(["--model", model])

    try:
        result = subprocess.run(
            cmd,
            input=diff,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise ReviewError(
            f"Claude review timed out after {timeout}s. "
            "Try increasing --timeout or review_timeout in config."
        )
    if result.returncode != 0:
        raise ReviewError(f"Claude review failed: {result.stderr.strip()}")
    return result.stdout.strip()
