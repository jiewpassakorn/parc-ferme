from __future__ import annotations

import re
from dataclasses import dataclass, fields
from datetime import date

from .github import PRInfo


@dataclass
class Colors:
    RED: str = "\033[0;31m"
    GREEN: str = "\033[0;32m"
    YELLOW: str = "\033[1;33m"
    BLUE: str = "\033[0;34m"
    BOLD: str = "\033[1m"
    NC: str = "\033[0m"

    @classmethod
    def none(cls) -> Colors:
        """Return a Colors instance with all codes set to empty strings."""
        return cls(**{f.name: "" for f in fields(cls)})


_NO_COLOR = Colors.none()


def get_colors(no_color: bool) -> Colors:
    if no_color:
        return _NO_COLOR
    return Colors()


def _escape_md(text: str) -> str:
    """Escape characters that have special meaning in markdown."""
    return re.sub(r'([\\`*_\{\}\[\]()#+\-.!|<>])', r'\\\1', text)


def format_header(pr_info: PRInfo, no_color: bool = False) -> str:
    c = get_colors(no_color)
    sep = f"{c.BLUE}{'━' * 66}{c.NC}"
    lines = [
        sep,
        f"{c.BLUE}🔍 Parc Fermé PR Review{c.NC}",
        sep,
        f"{c.GREEN}PR #{pr_info.number}:{c.NC} {pr_info.title}",
        f"{c.GREEN}Author:{c.NC} {pr_info.author}",
        f"{c.GREEN}Base:{c.NC} {pr_info.base_branch}",
        f"{c.GREEN}URL:{c.NC} {pr_info.url}",
    ]
    return "\n".join(lines)


def format_changed_files(files: list[str], no_color: bool = False) -> str:
    if not files:
        return ""
    c = get_colors(no_color)
    lines = [f"\n{c.YELLOW}📁 Changed files:{c.NC}"]
    for f in files:
        lines.append(f"   {f}")
    return "\n".join(lines)


def format_review_start(no_color: bool = False) -> str:
    c = get_colors(no_color)
    sep = f"{c.BLUE}{'━' * 66}{c.NC}"
    return f"\n{sep}\n{c.BLUE}🤖 Starting Claude Review...{c.NC}\n{sep}\n"


def format_review_end(no_color: bool = False) -> str:
    c = get_colors(no_color)
    sep = f"{c.BLUE}{'━' * 66}{c.NC}"
    return f"\n{sep}\n{c.GREEN}✅ Review complete{c.NC}"


def format_comment(
    pr_info: PRInfo,
    review: str,
    profile_name: str,
) -> str:
    today = date.today().isoformat()
    safe_title = _escape_md(pr_info.title)
    return (
        f"## 🔍 Parc Fermé PR Review — PR #{pr_info.number}: {safe_title}\n\n"
        f"**Profile**: `{profile_name}` | **Reviewed**: {today}\n\n"
        f"---\n\n"
        f"{review}\n\n"
        f"---\n"
        f"*Automated review by parc-ferme*"
    )
