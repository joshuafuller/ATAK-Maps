"""Console reporting and GitHub issue management for map validation results."""

from __future__ import annotations

import json
import subprocess

from mapvalidator.probe import ProbeResult, ProbeStatus
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


def print_report(
    validations: list[ValidationResult],
    probes: list[ProbeResult] | None = None,
) -> int:
    """Print a console report of validation (and optional probe) results.

    Returns an exit code: 1 if any validation errors exist, 0 otherwise.
    """
    # Build probe lookup by map name
    probe_map: dict[str, ProbeResult] = {}
    if probes:
        for p in probes:
            probe_map[p.map_name] = p

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

        # Probe status if available
        if vr.map_name in probe_map:
            pr = probe_map[vr.map_name]
            print(f"      PROBE: {pr.status.name}")

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

_UNHEALTHY = {ProbeStatus.BLOCKED, ProbeStatus.DEAD, ProbeStatus.DEGRADED}
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
    probes: list[ProbeResult],
    repo: str = "joshuafuller/ATAK-Maps",
) -> None:
    """Create or close GitHub issues based on probe results using the gh CLI."""
    if not probes:
        return

    open_issues = _find_open_issues(repo)

    for probe in probes:
        title_prefix = f"{_TITLE_PREFIX}{probe.map_name}"
        matching = [i for i in open_issues if i["title"].startswith(title_prefix)]

        if probe.status in _UNHEALTHY:
            # If there's already an open issue for this map, skip
            if matching:
                continue

            status_label = probe.status.name
            title = f"{_TITLE_PREFIX}{probe.map_name} \u2014 {status_label}"

            error_detail = probe.tak_error or probe.generic_error or "No error details"
            body_lines = [
                "## Map Health Alert",
                "",
                f"**Map:** {probe.map_name}",
                f"**Status:** {status_label}",
                f"**Test URL:** {probe.test_url}",
                f"**Error:** {error_detail}",
                "",
                "### Suggested Action",
                "Verify the tile server is still operational. "
                "If the server has permanently shut down, consider removing or "
                "replacing this map source.",
            ]
            body = "\n".join(body_lines)

            subprocess.run(
                [
                    "gh",
                    "issue",
                    "create",
                    "--title",
                    title,
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

        elif probe.status == ProbeStatus.HEALTHY and matching:
            # Close resolved issues
            for issue in matching:
                subprocess.run(
                    [
                        "gh",
                        "issue",
                        "close",
                        str(issue["number"]),
                        "--comment",
                        f"Map {probe.map_name} is now HEALTHY. Auto-closing.",
                        "--repo",
                        repo,
                    ],
                    capture_output=True,
                    text=True,
                )
