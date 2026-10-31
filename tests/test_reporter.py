"""Tests for mapvalidator.reporter module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mapvalidator.reporter import MapHealth, manage_github_issues, print_report
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
    """Weekly ATAK-harness results open and close "Map Health:" issues."""

    @staticmethod
    def _args(call):
        return " ".join(call[0][0] if call[0] else call.kwargs.get("args", []))

    @patch("mapvalidator.reporter.subprocess.run")
    def test_failing_map_opens_an_issue(self, mock_run):
        mock_run.return_value = MagicMock(stdout="[]", returncode=0)
        manage_github_issues([MapHealth("BrokenMap", "fail", "minZoom z3: HTTP 404")])
        assert mock_run.call_count == 2  # list, then create
        args = self._args(mock_run.call_args_list[1])
        assert "issue create" in args and "map-health" in args
        assert "Map Health: BrokenMap" in args and "HTTP 404" in args

    @patch("mapvalidator.reporter.subprocess.run")
    def test_no_duplicate_issue(self, mock_run):
        existing = [{"title": "Map Health: BrokenMap \u2014 DEAD", "number": 42}]
        mock_run.return_value = MagicMock(stdout=json.dumps(existing), returncode=0)
        manage_github_issues([MapHealth("BrokenMap", "fail", "HTTP 404")])
        assert mock_run.call_count == 1

    @patch("mapvalidator.reporter.subprocess.run")
    def test_recovered_map_closes_its_issue(self, mock_run):
        existing = [{"title": "Map Health: RecoveredMap \u2014 DEAD", "number": 99}]
        mock_run.return_value = MagicMock(stdout=json.dumps(existing), returncode=0)
        manage_github_issues([MapHealth("RecoveredMap", "ok", "")])
        assert mock_run.call_count == 2
        args = self._args(mock_run.call_args_list[1])
        assert "issue close" in args and "99" in args

    @patch("mapvalidator.reporter.subprocess.run")
    def test_warning_neither_opens_nor_closes(self, mock_run):
        existing = [{"title": "Map Health: SlowMap \u2014 not working", "number": 7}]
        mock_run.return_value = MagicMock(stdout=json.dumps(existing), returncode=0)
        manage_github_issues(
            [
                MapHealth("SlowMap", "warn", "blank tile at maxZoom"),
                MapHealth("NewWarn", "warn", "x"),
            ]
        )
        assert mock_run.call_count == 1

    @patch("mapvalidator.reporter.subprocess.run")
    def test_skipped_map_keeps_its_issue(self, mock_run):
        existing = [{"title": "Map Health: UK OS Road \u2014 not working", "number": 5}]
        mock_run.return_value = MagicMock(stdout=json.dumps(existing), returncode=0)
        manage_github_issues([MapHealth("UK OS Road", "skip", "needs an API key")])
        assert mock_run.call_count == 1  # list only: no close, no create

    @patch("mapvalidator.reporter.subprocess.run")
    def test_healthy_map_without_issue_does_nothing(self, mock_run):
        mock_run.return_value = MagicMock(stdout="[]", returncode=0)
        manage_github_issues([MapHealth("GoodMap", "ok", "")])
        assert all("create" not in self._args(c) for c in mock_run.call_args_list)

    @patch("mapvalidator.reporter.subprocess.run")
    def test_empty_list_makes_no_calls(self, mock_run):
        manage_github_issues([])
        mock_run.assert_not_called()
