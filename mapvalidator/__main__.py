import argparse
import sys
from pathlib import Path

from mapvalidator.probe import probe_all
from mapvalidator.reporter import manage_github_issues, print_report
from mapvalidator.xml_checks import check_duplicates, validate_corpus


def main():
    parser = argparse.ArgumentParser(
        description="ATAK Maps deep validation and liveness monitoring"
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help="Test tile server liveness (dual user-agent)",
    )
    parser.add_argument(
        "--issues",
        action="store_true",
        help="Create/close GitHub issues for probe failures",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick smoke test of a few reliable sources",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current)",
    )
    args = parser.parse_args()

    repo_dir = Path(args.directory).resolve()

    # Step 1: XML validation
    results = validate_corpus(repo_dir)
    dup_errors = check_duplicates(results)
    # Attach duplicate errors to the first result that matches each duplicate name
    for dup in dup_errors:
        # dup format: "Duplicate map name '...': file1, file2"
        # Just report as a standalone error on the first result
        if results:
            results[0].errors.append(dup)

    # Step 2: Liveness probing (optional)
    probes = None
    if args.probe or args.smoke:
        probes = probe_all(repo_dir, smoke_only=args.smoke)

    # Step 3: Report
    exit_code = print_report(results, probes)

    # If strict, treat warnings as errors
    if args.strict and any(r.warnings for r in results):
        exit_code = 1

    # Step 4: GitHub issues (optional)
    if args.issues and probes:
        manage_github_issues(probes)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
