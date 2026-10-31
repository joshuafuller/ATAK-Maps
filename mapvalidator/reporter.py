"""Console reporting and GitHub issue management for map validation results."""

from __future__ import annotations

import json
import subprocess

from dataclasses import dataclass

from mapvalidator.xml_checks import ValidationResult

# ---------------------------------------------------------------------------
# Console report
# ---------------------------------------------------------------------------

_STATUS_ORDER = {"error": 0, "warning": 1, "clean": 2}


def _classify(vr: ValidationResult) -> str:
    if vr.errors:
        return "error"
    if vr.warnings:
        return "warning"
    return "clean"


def print_report(validations: list[ValidationResult]) -> int:
    """Print a console report of validation results.

    Returns an exit code: 1 if any validation errors exist, 0 otherwise.
    """

    # Sort: errors first, then warnings, then clean
    sorted_vrs = sorted(validations, key=lambda v: _STATUS_ORDER.get(_classify(v), 9))

    total_errors = sum(len(v.errors) for v in validations)
    total_warnings = sum(len(v.warnings) for v in validations)

    # Header
    print("=" * 70)
    print("MAP VALIDATION REPORT")
    print("=" * 70)
    print()

    for vr in sorted_vrs:
        category = _classify(vr)
        symbol = {"error": "X", "warning": "!", "clean": "."}[category]
        print(f"[{symbol}] {vr.map_name}  ({vr.source_type})  — {vr.filepath}")

        for err in vr.errors:
            print(f"      ERROR: {err}")
        for warn in vr.warnings:
            print(f"      WARN:  {warn}")

        print()

    # Summary
    print("-" * 70)
    print(
        f"Errors: {total_errors}   Warnings: {total_warnings}   Files: {len(validations)}"
    )
    print("-" * 70)

    return 1 if total_errors > 0 else 0


# ---------------------------------------------------------------------------
# GitHub issue management
# ---------------------------------------------------------------------------


@dataclass
class MapHealth:
    """One map's result from the ATAK harness: status is ok, warn or fail."""

    name: str
    status: str
    problem: str


_TITLE_PREFIX = "Map Health: "


def _find_open_issues(repo: str) -> list[dict]:
    """Query open map-health issues via gh CLI."""
    result = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--label",
            "map-health",
            "--state",
            "open",
            "--json",
            "title,number",
            "--repo",
            repo,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return json.loads(result.stdout)


def manage_github_issues(
    health: list[MapHealth],
    repo: str = "joshuafuller/ATAK-Maps",
) -> None:
    """Open an issue for each failing map and close it when the map works again.

    Warnings neither open nor close issues. Titles start with "Map Health: <name>",
    so issues opened by the older liveness probe are found and closed too.
    """
    if not health:
        return

    open_issues = _find_open_issues(repo)

    for h in health:
        matching = [
            i for i in open_issues if i["title"].startswith(f"{_TITLE_PREFIX}{h.name}")
        ]
        if h.status == "fail" and not matching:
            body = "\n".join(
                [
                    "## Map Health Alert",
                    "",
                    f"**Map:** {h.name}",
                    f"**Problem:** {h.problem or 'No details'}",
                    "",
                    "Found by the weekly ATAK harness, which fetches tiles exactly as ATAK does.",
                    "Reproduce: `uv run python -m mapvalidator --harness . --only <map file>`",
                    "",
                    "### Suggested Action",
                    "Check the tile server. If it has shut down for good, remove or replace this map.",
                ]
            )
            subprocess.run(
                [
                    "gh",
                    "issue",
                    "create",
                    "--title",
                    f"{_TITLE_PREFIX}{h.name} \u2014 not working",
                    "--body",
                    body,
                    "--label",
                    "map-health",
                    "--repo",
                    repo,
                ],
                capture_output=True,
                text=True,
            )
        elif h.status == "ok":
            for issue in matching:
                subprocess.run(
                    [
                        "gh",
                        "issue",
                        "close",
                        str(issue["number"]),
                        "--comment",
                        f"{h.name} works in ATAK again (weekly ATAK harness). Auto-closing.",
                        "--repo",
                        repo,
                    ],
                    capture_output=True,
                    text=True,
                )
