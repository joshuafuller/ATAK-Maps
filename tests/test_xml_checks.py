"""Tests for mapvalidator.xml_checks module.

Tests are organized by check category. Synthetic XML fixtures are defined
in conftest.py; real repo XML files are discovered dynamically.
"""

from pathlib import Path

import pytest

from mapvalidator.xml_checks import (
    ValidationResult,
    check_duplicates,
    validate_corpus,
    validate_file,
)
from tests.conftest import (
    BGCOLOR_MULTI_HEX_XML,
    CAMELCASE_COORDSYS_XML,
    COMMA_SERVERPARTS_XML,
    COORDSYS_900913_XML,
    EMPTY_SERVERPARTS_NO_PLACEHOLDER_XML,
    EMPTY_URL_XML,
    HTTP_URL_XML,
    INVERT_Y_CAPITAL_TRUE_XML,
    INVERTED_ZOOM_XML,
    MAX_ZOOM_23_XML,
    MAX_ZOOM_26_XML,
    MISSING_TILETYPE_TMS_XML,
    MISSING_URL_PLACEHOLDERS_XML,
    NEGATIVE_MINZOOM_XML,
    QUADKEY_TMS_XML,
    SERVERPART_URL_NO_ELEMENT_XML,
    SERVERPARTS_ELEMENT_NO_URL_XML,
    TILE_UPDATE_IFNONEMATCH_XML,
    TILE_UPDATE_NONE_XML,
    TILE_UPDATE_NUMERIC_XML,
    UNKNOWN_TILETYPE_XML,
    VALID_TMS_XML,
    VALID_WMS_XML,
    VERSION_WHITESPACE_XML,
    WMS_ADDITIONALPARAMETERS_CORRECT_XML,
    WMS_ADITIONALPARAMETERS_TYPO_XML,
    WMS_MISSING_LAYERS_XML,
    WMS_MISSING_TILETYPE_XML,
    WMS_MISSING_VERSION_XML,
)

# ============================================================
# Helper
# ============================================================


def _has_message(messages: list[str], substring: str) -> bool:
    """Check if any message contains the given substring (case-insensitive)."""
    return any(substring.lower() in m.lower() for m in messages)


# ============================================================
# 1. Real XML corpus — all files parse without error
# ============================================================


class TestRealCorpus:
    def test_all_real_files_parse(self, real_xml_files):
        """Every real XML file should parse and produce a ValidationResult."""
        assert len(real_xml_files) > 0, "No XML files found in repo"
        for filepath in real_xml_files:
            result = validate_file(filepath)
            assert isinstance(
                result, ValidationResult
            ), f"{filepath} did not return ValidationResult"
            assert result.filepath == filepath
            assert result.map_name, f"{filepath} has empty map_name"

    def test_all_real_files_have_required_fields(self, real_xml_files):
        """Each real file should have a source_type set."""
        for filepath in real_xml_files:
            result = validate_file(filepath)
            assert result.source_type in (
                "TMS",
                "WMS",
                "Multi-Layer",
            ), f"{filepath}: unexpected source_type={result.source_type}"

    def test_all_tms_urls_have_valid_placeholders(self, real_xml_files):
        """Every TMS file should NOT have a missing-placeholder error."""
        for filepath in real_xml_files:
            result = validate_file(filepath)
            if result.source_type == "TMS":
                assert not _has_message(
                    result.errors, "missing placeholder"
                ), f"{filepath}: TMS URL missing placeholders; errors={result.errors}"

    def test_zoom_ranges_valid(self, real_xml_files):
        """All real files: minZoom <= maxZoom <= 25."""
        for filepath in real_xml_files:
            result = validate_file(filepath)
            assert not _has_message(
                result.errors, "minZoom"
            ), f"{filepath}: zoom error; errors={result.errors}"
            assert not _has_message(
                result.errors, "maxZoom"
            ), f"{filepath}: zoom error; errors={result.errors}"


# ============================================================
# 2. Valid files — no issues
# ============================================================


class TestValidFiles:
    def test_valid_tms(self, tmp_xml):
        result = validate_file(tmp_xml(VALID_TMS_XML))
        assert result.errors == []
        assert result.warnings == []
        assert result.source_type == "TMS"
        assert result.map_name == "Test TMS Map"

    def test_valid_wms(self, tmp_xml):
        result = validate_file(tmp_xml(VALID_WMS_XML))
        assert result.errors == []
        assert result.warnings == []
        assert result.source_type == "WMS"


# ============================================================
# 3. Zoom level checks
# ============================================================


class TestZoomLevels:
    def test_inverted_zoom_error(self, tmp_xml):
        result = validate_file(tmp_xml(INVERTED_ZOOM_XML))
        assert _has_message(result.errors, "minZoom")
        assert _has_message(result.errors, "maxZoom")

    def test_max_zoom_26_error(self, tmp_xml):
        result = validate_file(tmp_xml(MAX_ZOOM_26_XML))
        assert _has_message(result.errors, "maxZoom")
        assert _has_message(result.errors, "25")

    def test_max_zoom_23_warn_not_error(self, tmp_xml):
        result = validate_file(tmp_xml(MAX_ZOOM_23_XML))
        assert not _has_message(result.errors, "maxZoom")
        assert _has_message(result.warnings, "maxZoom")
        assert _has_message(result.warnings, "22")

    def test_negative_minzoom_error(self, tmp_xml):
        result = validate_file(tmp_xml(NEGATIVE_MINZOOM_XML))
        assert _has_message(result.errors, "minZoom")
        assert _has_message(result.errors, "negative") or _has_message(
            result.errors, "< 0"
        )


# ============================================================
# 4. TMS URL checks
# ============================================================


class TestTmsUrl:
    def test_missing_placeholders_error(self, tmp_xml):
        result = validate_file(tmp_xml(MISSING_URL_PLACEHOLDERS_XML))
        assert _has_message(result.errors, "placeholder")

    def test_empty_url_error(self, tmp_xml):
        result = validate_file(tmp_xml(EMPTY_URL_XML))
        assert _has_message(result.errors, "empty") or _has_message(
            result.errors, "url"
        )

    def test_quadkey_no_error(self, tmp_xml):
        """Bing-style {$q} quadkey should NOT produce a missing-placeholder error."""
        result = validate_file(tmp_xml(QUADKEY_TMS_XML))
        assert not _has_message(result.errors, "placeholder")
        assert result.source_type == "TMS"


# ============================================================
# 5. WMS checks
# ============================================================


class TestWmsChecks:
    def test_wms_missing_layers_error(self, tmp_xml):
        result = validate_file(tmp_xml(WMS_MISSING_LAYERS_XML))
        assert _has_message(result.errors, "layers")

    def test_wms_missing_tiletype_error(self, tmp_xml):
        result = validate_file(tmp_xml(WMS_MISSING_TILETYPE_XML))
        assert _has_message(result.errors, "tileType")

    def test_wms_missing_version_warn(self, tmp_xml):
        result = validate_file(tmp_xml(WMS_MISSING_VERSION_XML))
        assert not _has_message(result.errors, "version")
        assert _has_message(result.warnings, "version")


# ============================================================
# 6. Filename checks
# ============================================================


class TestFilenameChecks:
    def test_spaces_in_filename_error(self, tmp_xml):
        result = validate_file(tmp_xml(VALID_TMS_XML, filename="my map.xml"))
        assert _has_message(result.errors, "space")

    def test_non_ascii_filename_error(self, tmp_xml):
        result = validate_file(tmp_xml(VALID_TMS_XML, filename="m\u00e4p.xml"))
        assert _has_message(result.errors, "ascii") or _has_message(
            result.errors, "non-ascii"
        )


# ============================================================
# 7. Warning checks
# ============================================================


class TestWarnings:
    def test_camelcase_coordinate_system_warn(self, tmp_xml):
        result = validate_file(tmp_xml(CAMELCASE_COORDSYS_XML))
        assert _has_message(result.warnings, "coordinateSystem") or _has_message(
            result.warnings, "camelCase"
        )

    def test_comma_serverparts_warn(self, tmp_xml):
        result = validate_file(tmp_xml(COMMA_SERVERPARTS_XML))
        assert _has_message(result.warnings, "comma")

    def test_http_url_warn(self, tmp_xml):
        result = validate_file(tmp_xml(HTTP_URL_XML))
        assert _has_message(result.warnings, "http")

    def test_unknown_tiletype_warn(self, tmp_xml):
        result = validate_file(tmp_xml(UNKNOWN_TILETYPE_XML))
        assert _has_message(result.warnings, "tileType") or _has_message(
            result.warnings, "gif"
        )

    def test_invert_y_capital_true_warn(self, tmp_xml):
        result = validate_file(tmp_xml(INVERT_Y_CAPITAL_TRUE_XML))
        assert _has_message(result.warnings, "invertYCoordinate") or _has_message(
            result.warnings, "true"
        )


# ============================================================
# 8. serverParts / {$serverpart} mismatch
# ============================================================


class TestServerParts:
    def test_serverpart_url_no_element_error(self, tmp_xml):
        result = validate_file(tmp_xml(SERVERPART_URL_NO_ELEMENT_XML))
        assert _has_message(result.errors, "serverParts") or _has_message(
            result.errors, "serverpart"
        )

    def test_serverparts_element_no_url_error(self, tmp_xml):
        result = validate_file(tmp_xml(SERVERPARTS_ELEMENT_NO_URL_XML))
        assert _has_message(result.errors, "serverParts") or _has_message(
            result.errors, "serverpart"
        )


# ============================================================
# 9. Info checks
# ============================================================


class TestInfoChecks:
    def test_bgcolor_multi_hex_info(self, tmp_xml):
        result = validate_file(tmp_xml(BGCOLOR_MULTI_HEX_XML))
        assert _has_message(result.info, "backgroundColor") or _has_message(
            result.info, "hex"
        )

    def test_coordsys_900913_info(self, tmp_xml):
        result = validate_file(tmp_xml(COORDSYS_900913_XML))
        assert _has_message(result.info, "900913")

    def test_missing_tiletype_tms_info(self, tmp_xml):
        result = validate_file(tmp_xml(MISSING_TILETYPE_TMS_XML))
        assert _has_message(result.info, "tileType")


# ============================================================
# 10. Duplicate map names
# ============================================================


class TestDuplicates:
    def test_check_duplicates_finds_dupes(self, tmp_xml):
        r1 = ValidationResult(
            filepath=Path("/a/map1.xml"), map_name="Same Name", source_type="TMS"
        )
        r2 = ValidationResult(
            filepath=Path("/b/map2.xml"), map_name="Same Name", source_type="TMS"
        )
        r3 = ValidationResult(
            filepath=Path("/c/map3.xml"), map_name="Different Name", source_type="TMS"
        )
        errors = check_duplicates([r1, r2, r3])
        assert len(errors) >= 1
        assert _has_message(errors, "Same Name")
        assert not _has_message(errors, "Different Name")

    def test_no_duplicates(self):
        r1 = ValidationResult(
            filepath=Path("/a/map1.xml"), map_name="Name A", source_type="TMS"
        )
        r2 = ValidationResult(
            filepath=Path("/b/map2.xml"), map_name="Name B", source_type="TMS"
        )
        errors = check_duplicates([r1, r2])
        assert errors == []


# ============================================================
# 11. validate_corpus
# ============================================================


class TestValidateCorpus:
    def test_returns_results_for_all_files(self, repo_root):
        results = validate_corpus(repo_root)
        assert len(results) > 0
        for r in results:
            assert isinstance(r, ValidationResult)

    def test_corpus_count_matches_real_files(self, repo_root, real_xml_files):
        results = validate_corpus(repo_root)
        assert len(results) == len(real_xml_files)


# ============================================================
# 12. Bing Satellite specifically uses quadkey
# ============================================================

# ============================================================
# 13. Edge cases for full coverage
# ============================================================


class TestEdgeCases:
    def test_missing_max_zoom_error(self, tmp_xml):
        xml = """\
        <?xml version="1.0" encoding="UTF-8"?>
        <customMapSource>
            <name>No MaxZoom</name>
            <minZoom>0</minZoom>
            <tileType>png</tileType>
            <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
        </customMapSource>
        """
        result = validate_file(tmp_xml(xml))
        assert _has_message(result.errors, "maxZoom")

    def test_non_integer_maxzoom_error(self, tmp_xml):
        xml = """\
        <?xml version="1.0" encoding="UTF-8"?>
        <customMapSource>
            <name>Bad MaxZoom</name>
            <minZoom>0</minZoom>
            <maxZoom>abc</maxZoom>
            <tileType>png</tileType>
            <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
        </customMapSource>
        """
        result = validate_file(tmp_xml(xml))
        assert _has_message(result.errors, "maxZoom")
        assert _has_message(result.errors, "integer")

    def test_non_integer_minzoom_error(self, tmp_xml):
        xml = """\
        <?xml version="1.0" encoding="UTF-8"?>
        <customMapSource>
            <name>Bad MinZoom</name>
            <minZoom>xyz</minZoom>
            <maxZoom>18</maxZoom>
            <tileType>png</tileType>
            <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
        </customMapSource>
        """
        result = validate_file(tmp_xml(xml))
        assert _has_message(result.errors, "minZoom")
        assert _has_message(result.errors, "integer")

    def test_wms_empty_url_error(self, tmp_xml):
        xml = """\
        <?xml version="1.0" encoding="UTF-8"?>
        <customWmsMapSource>
            <name>WMS Empty URL</name>
            <minZoom>0</minZoom>
            <maxZoom>18</maxZoom>
            <tileType>png</tileType>
            <version>1.3.0</version>
            <layers>test</layers>
            <url></url>
        </customWmsMapSource>
        """
        result = validate_file(tmp_xml(xml))
        assert _has_message(result.errors, "url") or _has_message(
            result.errors, "empty"
        )

    def test_multi_layer_source_type(self, tmp_xml):
        xml = """\
        <?xml version="1.0" encoding="UTF-8"?>
        <customMultiLayerMapSource>
            <name>Multi Layer</name>
            <minZoom>0</minZoom>
            <maxZoom>18</maxZoom>
        </customMultiLayerMapSource>
        """
        result = validate_file(tmp_xml(xml))
        assert result.source_type == "Multi-Layer"

    def test_invalid_xml_parse_error(self, tmp_xml):
        xml = "this is not valid xml <<<"
        result = validate_file(tmp_xml(xml))
        assert _has_message(result.errors, "parse error") or _has_message(
            result.errors, "xml"
        )

    def test_srid_90094326_info(self, tmp_xml):
        xml = """\
        <?xml version="1.0" encoding="UTF-8"?>
        <customMapSource>
            <name>SRID 90094326</name>
            <minZoom>0</minZoom>
            <maxZoom>18</maxZoom>
            <tileType>png</tileType>
            <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
            <coordinatesystem>EPSG:90094326</coordinatesystem>
        </customMapSource>
        """
        result = validate_file(tmp_xml(xml))
        assert _has_message(result.info, "90094326")

    def test_check_duplicates_skips_unknown_names(self):
        r1 = ValidationResult(
            filepath=Path("/a.xml"), map_name="Unknown", source_type="TMS"
        )
        r2 = ValidationResult(
            filepath=Path("/b.xml"), map_name="Unknown", source_type="TMS"
        )
        errors = check_duplicates([r1, r2])
        assert errors == []


# ============================================================
# 12. Bing Satellite specifically uses quadkey
# ============================================================


class TestBingSatellite:
    def test_bing_satellite_no_placeholder_error(self, repo_root):
        bing_sat = repo_root / "Bing" / "Bing_Satellite.xml"
        if not bing_sat.exists():
            pytest.skip("Bing_Satellite.xml not in repo")
        result = validate_file(bing_sat)
        assert not _has_message(result.errors, "placeholder")
        assert result.source_type == "TMS"


# ============================================================
# 14. Real corpus — known issues produce expected diagnostics
# ============================================================


class TestKnownCorpusIssues:
    """Verify the validator catches the known issues documented in the spec."""

    def test_openseamap_no_camelcase_after_fix(self, repo_root):
        """openseamap files were fixed to use lowercase coordinatesystem — no warning."""
        seamarks = repo_root / "openseamap" / "openseamap_seamarks.xml"
        if not seamarks.exists():
            pytest.skip("openseamap_seamarks.xml not in repo")
        result = validate_file(seamarks)
        assert not _has_message(result.warnings, "coordinateSystem")
        assert not _has_message(result.warnings, "camelCase")

    def test_openseamap_no_comma_serverparts_after_fix(self, repo_root):
        """openseamap files were fixed to use space-separated serverParts — no warning."""
        seamarks = repo_root / "openseamap" / "openseamap_seamarks.xml"
        if not seamarks.exists():
            pytest.skip("openseamap_seamarks.xml not in repo")
        result = validate_file(seamarks)
        assert not _has_message(result.warnings, "comma")

    def test_google_hybrid_https_after_fix(self, repo_root):
        """Google hybrid was fixed to HTTPS — no warning."""
        hybrid = repo_root / "Google" / "google_hybrid.xml"
        if not hybrid.exists():
            pytest.skip("google_hybrid.xml not in repo")
        result = validate_file(hybrid)
        assert not _has_message(result.warnings, "http")

    def test_mtbmapcz_still_http(self, repo_root):
        """mtbmapcz stays HTTP (server doesn't support HTTPS) — should still warn."""
        mtb = repo_root / "mtbmapcz" / "mtbmapcz_mtb_map_europe.xml"
        if not mtb.exists():
            pytest.skip("mtbmapcz_mtb_map_europe.xml not in repo")
        result = validate_file(mtb)
        assert _has_message(result.warnings, "http")

    def test_canada_cbmt_maxzoom_23_warns(self, repo_root):
        """Canadian map with maxZoom=23 — should WARN (not ERROR)."""
        cbmt = repo_root / "NaturalResourcesCanada" / "naturalresourcescanada_cbmt.xml"
        if not cbmt.exists():
            pytest.skip("naturalresourcescanada_cbmt.xml not in repo")
        result = validate_file(cbmt)
        assert _has_message(result.warnings, "maxZoom")
        assert not _has_message(result.errors, "maxZoom")

    def test_bing_satellite_bgcolor_info(self, repo_root):
        """Bing Satellite has backgroundColor #000000 (6 hex digits) — must INFO."""
        bing = repo_root / "Bing" / "Bing_Satellite.xml"
        if not bing.exists():
            pytest.skip("Bing_Satellite.xml not in repo")
        result = validate_file(bing)
        assert _has_message(result.info, "backgroundColor")

    def test_real_tile_update_none_warns(self, repo_root):
        """Real files with <tileUpdate>None</tileUpdate> should produce a warning."""
        bing = repo_root / "Bing" / "Bing_Satellite.xml"
        if not bing.exists():
            pytest.skip("Bing_Satellite.xml not in repo")
        result = validate_file(bing)
        assert _has_message(result.warnings, "tileUpdate")


# ============================================================
# 15. tileUpdate non-numeric values
# ============================================================


class TestTileUpdate:
    def test_tile_update_none_warns(self, tmp_xml):
        """ATAK parser regex \\d+ silently ignores 'None' — should WARN."""
        result = validate_file(tmp_xml(TILE_UPDATE_NONE_XML))
        assert _has_message(result.warnings, "tileUpdate")
        assert _has_message(result.warnings, "numeric") or _has_message(
            result.warnings, "digits"
        )

    def test_tile_update_ifnonematch_warns(self, tmp_xml):
        """'IfNoneMatch' is also non-numeric — should WARN."""
        result = validate_file(tmp_xml(TILE_UPDATE_IFNONEMATCH_XML))
        assert _has_message(result.warnings, "tileUpdate")

    def test_tile_update_numeric_no_warning(self, tmp_xml):
        """Valid numeric tileUpdate (milliseconds) — no warning."""
        result = validate_file(tmp_xml(TILE_UPDATE_NUMERIC_XML))
        assert not _has_message(result.warnings, "tileUpdate")

    def test_no_tile_update_element_no_warning(self, tmp_xml):
        """Missing tileUpdate entirely — no warning (defaults to 0)."""
        result = validate_file(tmp_xml(VALID_TMS_XML))
        assert not _has_message(result.warnings, "tileUpdate")


# ============================================================
# 16. WMS aditionalparameters typo detection
# ============================================================


class TestAditionalParameters:
    def test_typo_spelling_info(self, tmp_xml):
        """ATAK accepts 'aditionalparameters' (typo) but should INFO."""
        result = validate_file(tmp_xml(WMS_ADITIONALPARAMETERS_TYPO_XML))
        assert _has_message(result.info, "aditionalparameters") or _has_message(
            result.info, "typo"
        )

    def test_correct_spelling_no_info(self, tmp_xml):
        """'additionalparameters' (correct) — no INFO about typo."""
        result = validate_file(tmp_xml(WMS_ADDITIONALPARAMETERS_CORRECT_XML))
        assert not _has_message(result.info, "typo")


# ============================================================
# 17. WMS version whitespace sensitivity
# ============================================================


class TestVersionWhitespace:
    def test_version_with_whitespace_warns(self, tmp_xml):
        """' 1.3.0 ' won't match ATAK's equals() — should WARN."""
        result = validate_file(tmp_xml(VERSION_WHITESPACE_XML))
        assert _has_message(result.warnings, "version") and _has_message(
            result.warnings, "whitespace"
        )


# ============================================================
# 18. Empty serverParts — no false positive
# ============================================================


class TestEmptyServerParts:
    def test_empty_serverparts_no_placeholder_no_error(self, tmp_xml):
        """Empty <serverParts></serverParts> with URL that doesn't use {$serverpart} — no error."""
        result = validate_file(tmp_xml(EMPTY_SERVERPARTS_NO_PLACEHOLDER_XML))
        assert not _has_message(result.errors, "serverParts")
        assert not _has_message(result.errors, "serverpart")
