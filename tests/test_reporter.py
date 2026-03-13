"""Tests for mapvalidator.reporter module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mapvalidator.probe import ProbeResult, ProbeStatus
from mapvalidator.reporter import manage_github_issues, print_report
from mapvalidator.xml_checks import ValidationResult

# ---------------------------------------------------------------------------
# Helpers to build test fixtures
# ---------------------------------------------------------------------------


def _vr(
    name: str = "TestMap",
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    info: list[str] | None = None,
) -> ValidationResult:
    """Shorthand factory for ValidationResult."""
    return ValidationResult(
        filepath=Path(f"Provider/{name}.xml"),
        map_name=name,
        source_type="TMS",
        errors=errors or [],
        warnings=warnings or [],
        info=info or [],
    )


def _pr(
    name: str = "TestMap",
    status: ProbeStatus = ProbeStatus.HEALTHY,
    tak_status_code: int | None = 200,
    tak_error: str | None = None,
    generic_status_code: int | None = 200,
    generic_error: str | None = None,
    test_url: str = "https://tiles.example.com/0/0/0.png",
) -> ProbeResult:
    """Shorthand factory for ProbeResult."""
    return ProbeResult(
        filepath=Path(f"Provider/{name}.xml"),
        map_name=name,
        status=status,
        tak_status_code=tak_status_code,
        tak_error=tak_error,
        generic_status_code=generic_status_code,
        generic_error=generic_error,
        test_url=test_url,
    )


# ===========================================================================
# print_report tests
# ===========================================================================


class TestPrintReportExitCode:
    """Tests for print_report return value (exit code)."""

    def test_errors_produce_exit_code_1(self):
        """ValidationResult with errors -> exit code 1."""
        vr = _vr(errors=["Missing <url> element"])
        assert print_report([vr]) == 1

    def test_clean_results_produce_exit_code_0(self):
        """ValidationResults with no errors -> exit code 0."""
        vr = _vr()
        assert print_report([vr]) == 0

    def test_warnings_do_not_cause_exit_code_1(self):
        """ValidationResult with only warnings -> exit code 0."""
        vr = _vr(warnings=["Uses HTTP instead of HTTPS"])
        assert print_report([vr]) == 0


class TestPrintReportOutput:
    """Tests for print_report console output content."""

    def test_output_includes_error_messages(self, capsys):
        """Error text should appear in the printed output."""
        vr = _vr(errors=["Missing <url> element"])
        print_report([vr])
        output = capsys.readouterr().out
        assert "Missing <url> element" in output

    def test_output_includes_warning_messages(self, capsys):
        """Warning text should appear in the printed output."""
        vr = _vr(warnings=["Uses HTTP instead of HTTPS"])
        print_report([vr])
        output = capsys.readouterr().out
        assert "Uses HTTP instead of HTTPS" in output

    def test_with_probes_shows_status(self, capsys):
        """When probes are provided, their status labels appear in output."""
        vr = _vr(name="AliveMap")
        pr_healthy = _pr(name="AliveMap", status=ProbeStatus.HEALTHY)
        vr2 = _vr(name="DeadMap")
        pr_dead = _pr(name="DeadMap", status=ProbeStatus.DEAD)

        print_report([vr, vr2], probes=[pr_healthy, pr_dead])
        output = capsys.readouterr().out
        assert "HEALTHY" in output
        assert "DEAD" in output

    def test_summary_counts(self, capsys):
        """Output must include error and warning counts."""
        vrs = [
            _vr(name="A", errors=["err1", "err2"]),
            _vr(name="B", warnings=["warn1"]),
            _vr(name="C"),
        ]
        print_report(vrs)
        output = capsys.readouterr().out
        assert "Errors: 2" in output
        assert "Warnings: 1" in output

    def test_errors_printed_before_warnings(self, capsys):
        """Spec: errors first, then warnings, then clean."""
        vrs = [
            _vr(name="CleanMap"),
            _vr(name="WarnMap", warnings=["some warning"]),
            _vr(name="ErrorMap", errors=["some error"]),
        ]
        print_report(vrs)
        output = capsys.readouterr().out
        error_pos = output.index("ErrorMap")
        warn_pos = output.index("WarnMap")
        clean_pos = output.index("CleanMap")
        assert error_pos < warn_pos < clean_pos


# ===========================================================================
# manage_github_issues tests
# ===========================================================================


class TestManageGithubIssues:
    """Tests for manage_github_issues GitHub issue management."""

    @patch("mapvalidator.reporter.subprocess.run")
    def test_creates_issue_for_dead_probe(self, mock_run):
        """DEAD probe should trigger gh issue create."""
        # gh issue list returns empty (no existing issues)
        mock_run.return_value = MagicMock(stdout="[]", returncode=0)

        probe = _pr(
            name="BrokenMap",
            status=ProbeStatus.DEAD,
            tak_error="Connection refused",
            test_url="https://tiles.example.com/0/0/0.png",
        )
        manage_github_issues([probe])

        # Should have called: 1) gh issue list, 2) gh issue create
        assert mock_run.call_count == 2
        create_call = mock_run.call_args_list[1]
        args = (
            create_call[0][0] if create_call[0] else create_call.kwargs.get("args", [])
        )
        args_str = " ".join(args)
        assert "issue" in args_str
        assert "create" in args_str
        assert "Map Health: BrokenMap" in args_str
        assert "DEAD" in args_str
        assert "map-health" in args_str

    @patch("mapvalidator.reporter.subprocess.run")
    def test_creates_issue_for_blocked_probe(self, mock_run):
        """BLOCKED probe should trigger gh issue create."""
        mock_run.return_value = MagicMock(stdout="[]", returncode=0)

        probe = _pr(
            name="BlockedMap",
            status=ProbeStatus.BLOCKED,
            tak_error="403 Forbidden",
            test_url="https://tiles.example.com/0/0/0.png",
        )
        manage_github_issues([probe])

        assert mock_run.call_count == 2
        create_call = mock_run.call_args_list[1]
        args = (
            create_call[0][0] if create_call[0] else create_call.kwargs.get("args", [])
        )
        args_str = " ".join(args)
        assert "issue" in args_str
        assert "create" in args_str
        assert "Map Health: BlockedMap" in args_str
        assert "BLOCKED" in args_str

    @patch("mapvalidator.reporter.subprocess.run")
    def test_no_issue_for_healthy_probe_no_existing(self, mock_run):
        """HEALTHY probe with no existing open issue -> no gh issue create."""
        mock_run.return_value = MagicMock(stdout="[]", returncode=0)

        probe = _pr(name="GoodMap", status=ProbeStatus.HEALTHY)
        manage_github_issues([probe])

        # Should only call gh issue list (to check for issues to close), never create
        for c in mock_run.call_args_list:
            args = c[0][0] if c[0] else c.kwargs.get("args", [])
            args_str = " ".join(args)
            assert "create" not in args_str

    @patch("mapvalidator.reporter.subprocess.run")
    def test_deduplication_no_duplicate_issue(self, mock_run):
        """If an open issue already exists with matching title, don't create a new one."""
        existing_issues = [{"title": "Map Health: BrokenMap \u2014 DEAD", "number": 42}]
        mock_run.return_value = MagicMock(
            stdout=json.dumps(existing_issues), returncode=0
        )

        probe = _pr(name="BrokenMap", status=ProbeStatus.DEAD)
        manage_github_issues([probe])

        # Should have called gh issue list but NOT gh issue create
        assert mock_run.call_count == 1  # only the list call
        args = mock_run.call_args_list[0][0][0]
        args_str = " ".join(args)
        assert "list" in args_str

    @patch("mapvalidator.reporter.subprocess.run")
    def test_auto_close_on_recovery(self, mock_run):
        """HEALTHY probe with existing open issue -> gh issue close with comment."""
        existing_issues = [
            {"title": "Map Health: RecoveredMap \u2014 DEAD", "number": 99}
        ]
        mock_run.return_value = MagicMock(
            stdout=json.dumps(existing_issues), returncode=0
        )

        probe = _pr(name="RecoveredMap", status=ProbeStatus.HEALTHY)
        manage_github_issues([probe])

        # Should have called: 1) gh issue list, 2) gh issue close
        assert mock_run.call_count == 2
        close_call = mock_run.call_args_list[1]
        args = close_call[0][0] if close_call[0] else close_call.kwargs.get("args", [])
        args_str = " ".join(args)
        assert "issue" in args_str
        assert "close" in args_str
        assert "99" in args_str

    @patch("mapvalidator.reporter.subprocess.run")
    def test_empty_probes_list(self, mock_run):
        """Empty probes list -> no subprocess calls at all."""
        manage_github_issues([])
        mock_run.assert_not_called()
