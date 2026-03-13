"""Integration tests for mapvalidator.__main__.main() CLI entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from mapvalidator.__main__ import main
from tests.conftest import INVERTED_ZOOM_XML, MAX_ZOOM_23_XML, VALID_TMS_XML

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_xml(tmp_path, xml_content, filename="test_map.xml"):
    """Write XML content into a file under tmp_path and return the directory."""
    f = tmp_path / filename
    f.write_text(xml_content.strip(), encoding="utf-8")
    return tmp_path


def _run_main(*cli_args):
    """Run main() with the given CLI args, returning the SystemExit code."""
    with patch.object(sys, "argv", ["mapvalidator", *cli_args]):
        with pytest.raises(SystemExit) as exc_info:
            main()
    return exc_info.value.code


# ---------------------------------------------------------------------------
# 1. Basic validation run — valid XML, no flags → exit 0
# ---------------------------------------------------------------------------


class TestBasicValidation:
    def test_valid_xml_exits_zero(self, tmp_path):
        _write_xml(tmp_path, VALID_TMS_XML)
        code = _run_main(str(tmp_path))
        assert code == 0

    def test_multiple_valid_files_exits_zero(self, tmp_path):
        _write_xml(tmp_path, VALID_TMS_XML, "map_a.xml")
        _write_xml(
            tmp_path, VALID_TMS_XML.replace("Test TMS Map", "Map B"), "map_b.xml"
        )
        code = _run_main(str(tmp_path))
        assert code == 0

    def test_invalid_xml_exits_one(self, tmp_path):
        """A file with inverted zoom levels produces errors → exit 1."""
        _write_xml(tmp_path, INVERTED_ZOOM_XML)
        code = _run_main(str(tmp_path))
        assert code == 1

    def test_empty_directory_exits_zero(self, tmp_path):
        """No XML files means no errors → exit 0."""
        code = _run_main(str(tmp_path))
        assert code == 0


# ---------------------------------------------------------------------------
# 2. --strict flag — warnings become errors → exit 1
# ---------------------------------------------------------------------------


class TestStrictFlag:
    def test_strict_with_warnings_exits_one(self, tmp_path):
        """maxZoom 23 produces a warning; --strict should turn it into exit 1."""
        _write_xml(tmp_path, MAX_ZOOM_23_XML)
        code = _run_main("--strict", str(tmp_path))
        assert code == 1

    def test_strict_without_warnings_exits_zero(self, tmp_path):
        """Clean file + --strict should still exit 0."""
        _write_xml(tmp_path, VALID_TMS_XML)
        code = _run_main("--strict", str(tmp_path))
        assert code == 0

    def test_no_strict_with_warnings_exits_zero(self, tmp_path):
        """Without --strict, warnings alone should not cause exit 1."""
        _write_xml(tmp_path, MAX_ZOOM_23_XML)
        code = _run_main(str(tmp_path))
        assert code == 0


# ---------------------------------------------------------------------------
# 3. Nonexistent directory — graceful handling
# ---------------------------------------------------------------------------


class TestNonexistentDirectory:
    def test_nonexistent_dir_exits_zero(self, tmp_path):
        """A path that doesn't exist has no XML files → exit 0 (empty results)."""
        bogus = str(tmp_path / "no_such_dir")
        code = _run_main(bogus)
        assert code == 0

    def test_nonexistent_dir_does_not_crash(self, tmp_path):
        """main() must not raise an unhandled exception for a missing dir."""
        bogus = str(tmp_path / "no_such_dir")
        # If we get here without an unhandled exception the test passes.
        code = _run_main(bogus)
        assert isinstance(code, int)


# ---------------------------------------------------------------------------
# 4. --probe flag — probe_all is called, network is mocked
# ---------------------------------------------------------------------------


class TestProbeFlag:
    @patch("mapvalidator.__main__.probe_all", return_value=[])
    def test_probe_calls_probe_all(self, mock_probe, tmp_path):
        _write_xml(tmp_path, VALID_TMS_XML)
        code = _run_main("--probe", str(tmp_path))
        mock_probe.assert_called_once()
        assert code == 0

    @patch("mapvalidator.__main__.probe_all", return_value=[])
    def test_smoke_calls_probe_all(self, mock_probe, tmp_path):
        _write_xml(tmp_path, VALID_TMS_XML)
        code = _run_main("--smoke", str(tmp_path))
        mock_probe.assert_called_once()
        assert code == 0

    @patch("mapvalidator.__main__.probe_all", return_value=[])
    def test_no_probe_flag_skips_probing(self, mock_probe, tmp_path):
        _write_xml(tmp_path, VALID_TMS_XML)
        code = _run_main(str(tmp_path))
        mock_probe.assert_not_called()
        assert code == 0


# ---------------------------------------------------------------------------
# 5. --issues flag — manage_github_issues is called, network is mocked
# ---------------------------------------------------------------------------


class TestIssuesFlag:
    @patch("mapvalidator.__main__.manage_github_issues")
    @patch("mapvalidator.__main__.probe_all", return_value=[MagicMock()])
    def test_issues_with_probe_calls_manage(self, mock_probe, mock_issues, tmp_path):
        _write_xml(tmp_path, VALID_TMS_XML)
        code = _run_main("--probe", "--issues", str(tmp_path))
        mock_issues.assert_called_once()
        assert code == 0

    @patch("mapvalidator.__main__.manage_github_issues")
    def test_issues_without_probe_skips_manage(self, mock_issues, tmp_path):
        """--issues alone (no --probe) means probes is None → skip manage."""
        _write_xml(tmp_path, VALID_TMS_XML)
        code = _run_main("--issues", str(tmp_path))
        mock_issues.assert_not_called()
        assert code == 0

    @patch("mapvalidator.__main__.manage_github_issues")
    @patch("mapvalidator.__main__.probe_all", return_value=[])
    def test_issues_with_empty_probes_skips_manage(
        self, mock_probe, mock_issues, tmp_path
    ):
        """--issues + --probe but probe_all returns [] (falsy) → skip manage."""
        _write_xml(tmp_path, VALID_TMS_XML)
        code = _run_main("--probe", "--issues", str(tmp_path))
        mock_issues.assert_not_called()
        assert code == 0


# ---------------------------------------------------------------------------
# 6. Default directory — uses cwd when no positional arg given
# ---------------------------------------------------------------------------


class TestDefaultDirectory:
    @patch("mapvalidator.__main__.validate_corpus")
    @patch("mapvalidator.__main__.check_duplicates", return_value=[])
    @patch("mapvalidator.__main__.print_report", return_value=0)
    def test_defaults_to_cwd(
        self, mock_report, mock_dup, mock_corpus, tmp_path, monkeypatch
    ):
        mock_corpus.return_value = []
        monkeypatch.chdir(tmp_path)
        _run_main()
        called_path = mock_corpus.call_args[0][0]
        assert called_path == tmp_path.resolve()
