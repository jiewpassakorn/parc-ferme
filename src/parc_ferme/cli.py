from __future__ import annotations

import argparse
import re
import sys

from . import __version__
from .config import load_config
from .errors import ParcFermeError, GitHubError
from .formatter import (
    format_changed_files,
    format_comment,
    format_header,
    format_review_end,
    format_review_start,
    get_colors,
)
from .github import (
    check_gh_available,
    get_changed_files,
    get_pr_diff,
    get_pr_info,
    post_comment,
)
from .profiles import get_profile, list_profiles
from .reviewer import MAX_DIFF_CHARS, build_prompt, check_claude_available, run_review


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="parc-ferme",
        description="Automated PR code reviews using Claude AI",
    )
    parser.add_argument(
        "pr",
        nargs="?",
        help="PR number or URL (e.g., 123 or https://github.com/owner/repo/pull/123)",
    )
    parser.add_argument(
        "-p", "--profile",
        default=None,
        help="Review profile to use (default/security/performance/angular)",
    )
    parser.add_argument(
        "-c", "--comment",
        action="store_true",
        help="Post review as PR comment",
    )
    parser.add_argument(
        "--comment-mode",
        choices=["create", "update"],
        default=None,
        help="Comment mode: 'create' new or 'update' last (default: create)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config file (overrides auto-discovery)",
    )
    parser.add_argument(
        "-R", "--repo",
        default=None,
        help="Repository in OWNER/REPO format (passed to gh)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List all available profiles and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the prompt that would be sent without calling Claude",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        metavar="FILE",
        help="Save review output to a file",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        metavar="SECONDS",
        help="Review timeout in seconds (default: 300)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if CRITICAL issues are found in the review",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored terminal output",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show debug information",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(argv)


def _has_critical_issues(review: str) -> bool:
    """Check if the review text contains CRITICAL severity markers."""
    return bool(re.search(r'\bCRITICAL\b', review))


def _print_err(msg: str, no_color: bool = False) -> None:
    c = get_colors(no_color)
    print(f"{c.RED}Error: {msg}{c.NC}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    c = get_colors(args.no_color)

    try:
        config = load_config(args.config)
    except ParcFermeError as e:
        _print_err(str(e), no_color=args.no_color)
        return 1

    custom_profiles = config.get("custom_profiles")

    # --list-profiles
    if args.list_profiles:
        all_profiles = list_profiles(custom_profiles)
        print("Available profiles:\n")
        for name, profile in sorted(all_profiles.items()):
            print(f"  {name:15s}  {profile.description}")
        return 0

    # PR is required for all other operations
    if not args.pr:
        _print_err("PR number or URL is required. Use --help for usage.", no_color=args.no_color)
        return 1

    try:
        check_gh_available()
        if not args.dry_run:
            check_claude_available()
    except ParcFermeError as e:
        _print_err(str(e), no_color=args.no_color)
        return 1

    # Resolve profile
    profile_name = args.profile or config.get("default_profile", "default")

    try:
        profile = get_profile(profile_name, custom_profiles)
    except ValueError as e:
        _print_err(str(e), no_color=args.no_color)
        return 1

    try:
        # Fetch PR info
        pr_info = get_pr_info(args.pr, repo=args.repo)
        print(format_header(pr_info, no_color=args.no_color))

        # Changed files
        changed_files = get_changed_files(args.pr, repo=args.repo)
        changed_files_output = format_changed_files(changed_files, no_color=args.no_color)
        if changed_files_output:
            print(changed_files_output)

        # Build prompt
        prompt = build_prompt(pr_info, profile)

        if args.verbose:
            print(f"\n{c.YELLOW}[verbose] Profile: {profile_name}{c.NC}")
            print(f"{c.YELLOW}[verbose] Model: {config.get('claude_model', 'default')}{c.NC}")

        # Dry run
        if args.dry_run:
            print(f"\n{c.YELLOW}--- DRY RUN: Prompt that would be sent ---{c.NC}\n")
            print(prompt)
            print(f"\n{c.YELLOW}--- End of prompt (diff would follow via stdin) ---{c.NC}")
            return 0

        # Run review
        print(format_review_start(no_color=args.no_color))

        diff = get_pr_diff(args.pr, repo=args.repo)

        if len(diff) > MAX_DIFF_CHARS:
            print(
                f"\n{c.YELLOW}\u26a0\ufe0f  Diff is {len(diff):,} chars, exceeding "
                f"{MAX_DIFF_CHARS:,} limit. It will be truncated.{c.NC}"
            )

        timeout = args.timeout or config.get("review_timeout", 300)
        review = run_review(
            prompt,
            diff,
            model=config.get("claude_model"),
            timeout=timeout,
        )
        print(review)
        print(format_review_end(no_color=args.no_color))

        # Save to file
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(review)
                    f.write("\n")
                print(f"\n{c.GREEN}\U0001f4c4 Review saved to {args.output}{c.NC}")
            except OSError as e:
                print(
                    f"\n{c.YELLOW}Could not write to {args.output}: {e}{c.NC}",
                    file=sys.stderr,
                )

        # Auto-comment
        should_comment = args.comment or config.get("comment", {}).get("enabled", False)
        if should_comment:
            comment_mode = args.comment_mode or config.get("comment", {}).get("mode", "create")
            comment_body = format_comment(pr_info, review, profile_name)
            try:
                post_comment(
                    args.pr,
                    comment_body,
                    repo=args.repo,
                    edit_last=(comment_mode == "update"),
                )
                print(f"\n{c.GREEN}\U0001f4ac Review posted as PR comment{c.NC}")
            except GitHubError as e:
                print(f"\n{c.YELLOW}\u26a0\ufe0f  Could not post comment: {e}{c.NC}", file=sys.stderr)

        # Strict mode
        if args.strict and _has_critical_issues(review):
            print(f"\n{c.RED}Strict mode: CRITICAL issues found, exiting with code 1{c.NC}")
            return 1

    except ParcFermeError as e:
        _print_err(str(e), no_color=args.no_color)
        return 1
    except KeyboardInterrupt:
        print(f"\n{c.RED}Review cancelled.{c.NC}")
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
