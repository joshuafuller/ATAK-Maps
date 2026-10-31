import argparse
import sys
from pathlib import Path

from mapvalidator.reporter import MapHealth, manage_github_issues, print_report
from mapvalidator.xml_checks import check_duplicates, validate_corpus


def main():
    parser = argparse.ArgumentParser(
        description="ATAK Maps deep validation and liveness monitoring"
    )
    parser.add_argument(
        "--issues",
        action="store_true",
        help="With --harness: open/close GitHub 'Map Health' issues for failing maps",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )
    parser.add_argument(
        "--harness",
        action="store_true",
        help="Fetch tiles exactly as ATAK does at min/max zoom and check content",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        type=Path,
        help="With --harness: check only these map files",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="With --harness: also write per-map health (for the site's map explorer) to this file",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current)",
    )
    args = parser.parse_args()

    repo_dir = Path(args.directory).resolve()

    if args.harness:
        from mapvalidator import harness

        results = harness.run_harness(repo_dir, harness.http_fetch, only=args.only)
        report, exit_code = harness.format_report(results)
        print(report)
        # Health first: the site's status must not depend on the issue step.
        if args.json:
            import json
            from datetime import datetime, timezone

            checked = datetime.now(timezone.utc).isoformat(timespec="seconds")
            args.json.write_text(
                json.dumps(harness.health_report(results, checked), indent=1) + "\n"
            )
        if args.issues:
            from mapvalidator.atak_source import parse_source
            from mapvalidator.catalog import map_slug

            health = harness.health_report(results, "")
            manage_github_issues(
                [
                    MapHealth(
                        parse_source(repo_dir / path).name or path.stem,
                        health[map_slug(path)]["status"],
                        health[map_slug(path)]["problem"],
                    )
                    for path in results
                ]
            )
        sys.exit(exit_code)

    # Step 1: XML validation
    results = validate_corpus(repo_dir)
    dup_errors = check_duplicates(results)
    # Attach duplicate errors to the first result that matches each duplicate name
    for dup in dup_errors:
        # dup format: "Duplicate map name '...': file1, file2"
        # Just report as a standalone error on the first result
        if results:
            results[0].errors.append(dup)

    # Step 3: Report
    exit_code = print_report(results)

    # If strict, treat warnings as errors
    if args.strict and any(r.warnings for r in results):
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
