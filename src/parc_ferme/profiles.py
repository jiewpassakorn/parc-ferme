from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SeverityLevel:
    emoji: str
    label: str
    description: str


@dataclass
class Profile:
    name: str
    description: str
    system_role: str
    rules: list[str]
    checks: list[str]
    severity_levels: list[SeverityLevel] = field(default_factory=list)
    output_format: str = "[SEVERITY] file:line — description"
    extra_instructions: str = ""


DEFAULT_SEVERITY_LEVELS = [
    SeverityLevel("\U0001f534", "CRITICAL", "Must fix before merge"),
    SeverityLevel("\U0001f7e1", "WARNING", "Should fix, potential issue"),
    SeverityLevel("\U0001f535", "INFO", "Nice to fix, minor improvement"),
]


BUILTIN_PROFILES: dict[str, Profile] = {
    "default": Profile(
        name="default",
        description="General code review",
        system_role="senior code reviewer",
        rules=[
            "Only flag REAL issues, not style preferences",
            "Be concise, no filler, no praise",
            "If no issues found, just say: ✅ LGTM",
        ],
        checks=[
            "Bugs: Logic errors, null/undefined issues, incorrect types",
            "Security: XSS, injection, exposed secrets",
            "Breaking changes: Public API changes, backward compatibility",
            "Code smells: Dead code, duplicated logic, overly complex conditions",
            "Typos: In code identifiers and user-facing strings",
        ],
        severity_levels=DEFAULT_SEVERITY_LEVELS,
    ),
    "security": Profile(
        name="security",
        description="Security-focused review",
        system_role="application security specialist",
        rules=[
            "Focus ONLY on security issues, ignore style and conventions",
            "Be concise, no filler, no praise",
            "If no issues found, just say: ✅ LGTM - No security issues found",
        ],
        checks=[
            "XSS: unsafe innerHTML, bypassSecurityTrust*, template injection",
            "Injection: SQL/NoSQL injection, command injection, LDAP injection",
            "Secrets: Hardcoded credentials, API keys, tokens in source code",
            "CSRF: Missing CSRF protection on state-changing endpoints",
            "Auth bypass: Broken authentication, improper authorization checks",
            "Path traversal: Unsanitized file paths, directory traversal",
            "SSRF: Server-side request forgery via user-controlled URLs",
            "Insecure deserialization: Unsafe JSON.parse on untrusted data",
            "Prototype pollution: Unsafe object merging or property assignment",
            "eval/Function: Dynamic code execution with user input",
        ],
        severity_levels=DEFAULT_SEVERITY_LEVELS,
    ),
    "performance": Profile(
        name="performance",
        description="Performance-focused review",
        system_role="performance engineer",
        rules=[
            "Focus ONLY on performance issues, ignore style and conventions",
            "Be concise, no filler, no praise",
            "If no issues found, just say: ✅ LGTM - No performance issues found",
        ],
        checks=[
            "Memory leaks: Unsubscribed observables, detached DOM references, unclosed resources",
            "N+1 queries: Database calls in loops, repeated API calls",
            "Bundle size: Large imports that could be tree-shaken or lazy loaded",
            "Unnecessary re-renders: Missing trackBy, excessive change detection",
            "Algorithm complexity: O(n²) or worse when O(n) is possible",
            "Missing caching: Repeated expensive computations without memoization",
            "Large payloads: Fetching unnecessary data, missing pagination",
            "Blocking operations: Synchronous I/O, long-running main thread tasks",
        ],
        severity_levels=DEFAULT_SEVERITY_LEVELS,
    ),
    "angular": Profile(
        name="angular",
        description="Angular/TypeScript specific review",
        system_role="senior Angular/TypeScript code reviewer",
        rules=[
            "Only flag REAL issues, not style preferences",
            "Be concise, no filler, no praise",
            "If no issues found, just say: ✅ LGTM",
        ],
        checks=[
            "Bugs: Logic errors, null/undefined issues, incorrect types",
            "Security: XSS, injection, exposed secrets, unsafe innerHTML",
            "Breaking changes: Public API changes, module federation exports",
            "Performance: Memory leaks (unsubscribed observables), unnecessary re-renders",
            "Angular anti-patterns: Missing OnDestroy cleanup, improper change detection",
            "RxJS issues: Missing unsubscribe, improper operators, nested subscribes",
            "TypeScript: 'any' type abuse, missing null checks",
            "Typos: In code identifiers and user-facing strings",
        ],
        severity_levels=DEFAULT_SEVERITY_LEVELS,
    ),
}


def get_profile(name: str, custom_profiles: dict[str, Profile] | None = None) -> Profile:
    all_profiles = {**BUILTIN_PROFILES}
    if custom_profiles:
        all_profiles.update(custom_profiles)

    if name not in all_profiles:
        available = ", ".join(sorted(all_profiles.keys()))
        raise ValueError(f"Unknown profile '{name}'. Available: {available}")
    return all_profiles[name]


def list_profiles(custom_profiles: dict[str, Profile] | None = None) -> dict[str, Profile]:
    all_profiles = {**BUILTIN_PROFILES}
    if custom_profiles:
        all_profiles.update(custom_profiles)
    return all_profiles


def parse_severity_levels(raw: list[dict[str, Any]]) -> list[SeverityLevel]:
    """Convert raw YAML severity level dicts to SeverityLevel objects."""
    return [
        SeverityLevel(
            emoji=item.get("emoji", ""),
            label=item.get("label", ""),
            description=item.get("description", ""),
        )
        for item in raw
    ]


def merge_profile(base: Profile, overrides: dict) -> Profile:
    """Create a new profile by extending a base profile with overrides."""
    raw_levels = overrides.get("severity_levels")
    if isinstance(raw_levels, list) and raw_levels:
        if isinstance(raw_levels[0], dict):
            severity_levels = parse_severity_levels(raw_levels)
        elif isinstance(raw_levels[0], SeverityLevel):
            severity_levels = raw_levels
        else:
            severity_levels = base.severity_levels
    else:
        severity_levels = base.severity_levels

    return Profile(
        name=overrides.get("name", base.name),
        description=overrides.get("description", base.description),
        system_role=overrides.get("system_role", base.system_role),
        rules=overrides.get("rules", base.rules),
        checks=overrides.get("checks", base.checks),
        severity_levels=severity_levels,
        output_format=overrides.get("output_format", base.output_format),
        extra_instructions="\n".join(
            filter(None, [
                base.extra_instructions,
                overrides.get("extra_instructions", ""),
            ])
        ),
    )
