"""Tests for mapvalidator.probe module."""

import xml.etree.ElementTree as ET
from pathlib import Path

import re

import responses
from requests.exceptions import ConnectionError, Timeout

from mapvalidator.probe import (
    SMOKE_SOURCES,
    TAK_USER_AGENT,
    ProbeResult,
    ProbeStatus,
    _tile_to_quadkey,
    build_test_urls,
    classify,
    probe_all,
    probe_smoke,
    probe_source,
    probe_url,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _xml(text: str) -> ET.Element:
    """Parse XML string into an Element."""
    return ET.fromstring(text.strip())


TMS_XYZ_XML = """
<customMapSource>
    <name>Test TMS</name>
    <minZoom>2</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

TMS_QUADKEY_XML = """
<customMapSource>
    <name>Bing - Satellite</name>
    <minZoom>0</minZoom>
    <maxZoom>20</maxZoom>
    <tileType>jpg</tileType>
    <url>https://ecn.t2.tiles.virtualearth.net/tiles/a{$q}?g=761</url>
</customMapSource>
"""

TMS_SERVERPARTS_XML = """
<customMapSource>
    <name>OpenSeaMap</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://{$serverpart}.openseamap.org/seamark/{$z}/{$x}/{$y}.png</url>
    <serverParts>t1 t2 t3</serverParts>
</customMapSource>
"""

WMS_111_XML = """
<customWmsMapSource>
    <name>Canada Base Map</name>
    <version>1.1.1</version>
    <minZoom>0</minZoom>
    <maxZoom>23</maxZoom>
    <tileType>jpg</tileType>
    <url>https://maps.geogratis.gc.ca/wms/CBMT?</url>
    <coordinatesystem>EPSG:3857</coordinatesystem>
    <layers>CBMT</layers>
</customWmsMapSource>
"""

WMS_130_XML = """
<customWmsMapSource>
    <name>WMS 1.3.0 Source</name>
    <version>1.3.0</version>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://wms.example.com/service?</url>
    <coordinatesystem>EPSG:4326</coordinatesystem>
    <layers>layer1</layers>
</customWmsMapSource>
"""

EMPTY_URL_XML = """
<customMapSource>
    <name>Empty URL</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>  </url>
</customMapSource>
"""


# ---------------------------------------------------------------------------
# 0. _tile_to_quadkey
# ---------------------------------------------------------------------------


class TestTileToQuadkey:
    def test_zoom_0_returns_zero(self):
        assert _tile_to_quadkey(0, 0, 0) == "0"

    def test_zoom_1_tiles(self):
        assert _tile_to_quadkey(1, 0, 0) == "0"
        assert _tile_to_quadkey(1, 1, 0) == "1"
        assert _tile_to_quadkey(1, 0, 1) == "2"
        assert _tile_to_quadkey(1, 1, 1) == "3"

    def test_zoom_3_western_europe(self):
        # tile (4, 2) at zoom 3 -> quadkey "120"
        assert _tile_to_quadkey(3, 4, 2) == "120"


# ---------------------------------------------------------------------------
# 1. build_test_urls — TMS with XYZ
# ---------------------------------------------------------------------------


class TestBuildTestUrlsTmsXyz:
    def test_returns_urls_with_zoom_levels_substituted(self):
        root = _xml(TMS_XYZ_XML)
        urls = build_test_urls(root)
        assert len(urls) > 0
        # minZoom=2 at (0,0), zoom 3 at populated coords, zoom 0, zoom 8
        assert "https://tiles.example.com/2/0/0.png" in urls
        assert "https://tiles.example.com/3/4/2.png" in urls  # W. Europe
        assert "https://tiles.example.com/3/2/3.png" in urls  # E. US
        assert "https://tiles.example.com/0/0/0.png" in urls
        assert "https://tiles.example.com/8/134/86.png" in urls  # C. Europe

    def test_no_unresolved_placeholders(self):
        root = _xml(TMS_XYZ_XML)
        urls = build_test_urls(root)
        for url in urls:
            assert "{$" not in url


# ---------------------------------------------------------------------------
# 2. build_test_urls — TMS with quadkey
# ---------------------------------------------------------------------------


class TestBuildTestUrlsQuadkey:
    def test_returns_urls_with_quadkey_substituted(self):
        root = _xml(TMS_QUADKEY_XML)
        urls = build_test_urls(root)
        assert len(urls) > 0
        # minZoom=0 at (0,0) -> quadkey "0"
        assert any("tiles/a0?" in u for u in urls)
        # zoom 3, tile (4,2) -> quadkey "120" (W. Europe)
        assert any("tiles/a120?" in u for u in urls)

    def test_no_unresolved_placeholders(self):
        root = _xml(TMS_QUADKEY_XML)
        urls = build_test_urls(root)
        for url in urls:
            assert "{$q}" not in url


# ---------------------------------------------------------------------------
# 3. build_test_urls — TMS with serverParts
# ---------------------------------------------------------------------------


class TestBuildTestUrlsServerParts:
    def test_first_server_part_substituted(self):
        root = _xml(TMS_SERVERPARTS_XML)
        urls = build_test_urls(root)
        assert len(urls) > 0
        for url in urls:
            assert "t1.openseamap.org" in url, f"serverpart not substituted in {url}"
            assert "{$serverpart}" not in url


# ---------------------------------------------------------------------------
# 4. build_test_urls — WMS 1.1.1
# ---------------------------------------------------------------------------


class TestBuildTestUrlsWms:
    def test_returns_getmap_url_with_correct_params(self):
        root = _xml(WMS_111_XML)
        urls = build_test_urls(root)
        assert len(urls) == 1
        url = urls[0]
        assert "SERVICE=WMS" in url
        assert "REQUEST=GetMap" in url
        assert "VERSION=1.1.1" in url
        assert "SRS=EPSG:3857" in url
        assert "LAYERS=CBMT" in url
        assert "BBOX=-180,-90,180,90" in url
        assert "WIDTH=256" in url
        assert "HEIGHT=256" in url
        assert "FORMAT=image/jpeg" in url
        assert "STYLES=" in url

    def test_wms_no_crs_param(self):
        """WMS 1.1.1 should use SRS, not CRS."""
        root = _xml(WMS_111_XML)
        urls = build_test_urls(root)
        url = urls[0]
        assert "SRS=" in url
        assert "CRS=" not in url


# ---------------------------------------------------------------------------
# 5. build_test_urls — WMS version 1.3.0
# ---------------------------------------------------------------------------


class TestBuildTestUrlsWms130:
    def test_uses_crs_instead_of_srs(self):
        root = _xml(WMS_130_XML)
        urls = build_test_urls(root)
        assert len(urls) == 1
        url = urls[0]
        assert "CRS=" in url
        assert "SRS=" not in url
        assert "VERSION=1.3.0" in url

    def test_epsg4326_becomes_crs84_for_130(self):
        """ATAK source: version 1.3.x converts EPSG:4326 to CRS:84."""
        root = _xml(WMS_130_XML)
        urls = build_test_urls(root)
        url = urls[0]
        assert "CRS=CRS:84" in url
        assert "EPSG:4326" not in url


# ---------------------------------------------------------------------------
# 6. build_test_urls — empty URL
# ---------------------------------------------------------------------------


class TestBuildTestUrlsEmptyUrl:
    def test_returns_empty_list(self):
        root = _xml(EMPTY_URL_XML)
        urls = build_test_urls(root)
        assert urls == []


# ---------------------------------------------------------------------------
# 7. probe_url — 200 + image/png
# ---------------------------------------------------------------------------


class TestProbeUrl200Image:
    @responses.activate
    def test_returns_200_none_true_with_content_length(self):
        tile_body = b"\x89PNG\r\n" + b"\x00" * 100
        responses.add(
            responses.GET,
            "https://tiles.example.com/0/0/0.png",
            body=tile_body,
            status=200,
            content_type="image/png",
        )
        status, error, is_image, content_length = probe_url(
            "https://tiles.example.com/0/0/0.png", TAK_USER_AGENT
        )
        assert status == 200
        assert error is None
        assert is_image is True
        assert content_length == len(tile_body)


# ---------------------------------------------------------------------------
# 8. probe_url — 200 + text/html (not an image)
# ---------------------------------------------------------------------------


class TestProbeUrl200Html:
    @responses.activate
    def test_returns_200_none_false(self):
        html_body = b"<html>not a tile</html>"
        responses.add(
            responses.GET,
            "https://tiles.example.com/0/0/0.png",
            body=html_body,
            status=200,
            content_type="text/html",
        )
        status, error, is_image, content_length = probe_url(
            "https://tiles.example.com/0/0/0.png", TAK_USER_AGENT
        )
        assert status == 200
        assert error is None
        assert is_image is False
        assert content_length == len(html_body)


# ---------------------------------------------------------------------------
# 9. probe_url — 403
# ---------------------------------------------------------------------------


class TestProbeUrl403:
    @responses.activate
    def test_returns_403_with_error(self):
        responses.add(
            responses.GET,
            "https://tiles.example.com/0/0/0.png",
            body=b"Forbidden",
            status=403,
        )
        status, error, is_image, content_length = probe_url(
            "https://tiles.example.com/0/0/0.png", TAK_USER_AGENT
        )
        assert status == 403
        assert error is not None
        assert is_image is False
        assert content_length == 0


# ---------------------------------------------------------------------------
# 10. probe_url — 404
# ---------------------------------------------------------------------------


class TestProbeUrl404:
    @responses.activate
    def test_returns_404_with_error(self):
        responses.add(
            responses.GET,
            "https://tiles.example.com/0/0/0.png",
            body=b"Not Found",
            status=404,
        )
        status, error, is_image, content_length = probe_url(
            "https://tiles.example.com/0/0/0.png", TAK_USER_AGENT
        )
        assert status == 404
        assert error is not None
        assert is_image is False
        assert content_length == 0


# ---------------------------------------------------------------------------
# 11. probe_url — 500
# ---------------------------------------------------------------------------


class TestProbeUrl500:
    @responses.activate
    def test_returns_500_with_error(self):
        responses.add(
            responses.GET,
            "https://tiles.example.com/0/0/0.png",
            body=b"Internal Server Error",
            status=500,
        )
        status, error, is_image, content_length = probe_url(
            "https://tiles.example.com/0/0/0.png", TAK_USER_AGENT
        )
        assert status == 500
        assert error is not None
        assert is_image is False
        assert content_length == 0


# ---------------------------------------------------------------------------
# 12. probe_url — ConnectionError (DNS failure)
# ---------------------------------------------------------------------------


class TestProbeUrlConnectionError:
    @responses.activate
    def test_returns_none_with_error(self):
        responses.add(
            responses.GET,
            "https://tiles.example.com/0/0/0.png",
            body=ConnectionError("DNS resolution failed"),
        )
        status, error, is_image, content_length = probe_url(
            "https://tiles.example.com/0/0/0.png", TAK_USER_AGENT
        )
        assert status is None
        assert error is not None
        assert "DNS" in error or "Connection" in error or "connection" in error
        assert is_image is False
        assert content_length == 0


# ---------------------------------------------------------------------------
# 13. probe_url — Timeout
# ---------------------------------------------------------------------------


class TestProbeUrlTimeout:
    @responses.activate
    def test_returns_none_with_error(self):
        responses.add(
            responses.GET,
            "https://tiles.example.com/0/0/0.png",
            body=Timeout("Request timed out"),
        )
        status, error, is_image, content_length = probe_url(
            "https://tiles.example.com/0/0/0.png", TAK_USER_AGENT
        )
        assert status is None
        assert error is not None
        assert is_image is False
        assert content_length == 0


# ---------------------------------------------------------------------------
# 14. classify — both healthy
# ---------------------------------------------------------------------------


class TestClassifyHealthy:
    def test_both_200_image_returns_healthy(self):
        tak = (200, None, True, 15000)
        generic = (200, None, True, 15000)
        assert classify(tak, generic) == ProbeStatus.HEALTHY

    def test_both_200_image_similar_size_returns_healthy(self):
        """Images with similar sizes (within 2x) are HEALTHY."""
        tak = (200, None, True, 12000)
        generic = (200, None, True, 15000)
        assert classify(tak, generic) == ProbeStatus.HEALTHY


# ---------------------------------------------------------------------------
# 15. classify — TAK blocked, generic ok
# ---------------------------------------------------------------------------


class TestClassifyBlocked:
    def test_tak_403_generic_ok_returns_blocked(self):
        tak = (403, "HTTP 403", False, 0)
        generic = (200, None, True, 15000)
        assert classify(tak, generic) == ProbeStatus.BLOCKED

    def test_tak_429_generic_ok_returns_blocked(self):
        tak = (429, "HTTP 429", False, 0)
        generic = (200, None, True, 15000)
        assert classify(tak, generic) == ProbeStatus.BLOCKED

    def test_soft_block_both_200_image_but_different_content(self):
        """OSM-style soft block: both return 200+image/png but TAK gets a
        'blocked' notice image (6987 bytes) while generic gets a real tile
        (15189 bytes).  The size divergence signals a soft block."""
        tak = (200, None, True, 6987)
        generic = (200, None, True, 15189)
        assert classify(tak, generic) == ProbeStatus.BLOCKED

    def test_soft_block_tak_much_smaller(self):
        """TAK image much smaller than generic — likely an error tile."""
        tak = (200, None, True, 100)
        generic = (200, None, True, 50000)
        assert classify(tak, generic) == ProbeStatus.BLOCKED

    def test_soft_block_tak_much_larger(self):
        """TAK image much larger than generic (e.g. verbose error page PNG)."""
        tak = (200, None, True, 50000)
        generic = (200, None, True, 103)
        assert classify(tak, generic) == ProbeStatus.BLOCKED


# ---------------------------------------------------------------------------
# 16. classify — both fail
# ---------------------------------------------------------------------------


class TestClassifyDead:
    def test_both_fail_returns_dead(self):
        tak = (None, "Connection failed", False, 0)
        generic = (None, "Connection failed", False, 0)
        assert classify(tak, generic) == ProbeStatus.DEAD

    def test_both_non_200_returns_dead(self):
        tak = (500, "HTTP 500", False, 0)
        generic = (500, "HTTP 500", False, 0)
        assert classify(tak, generic) == ProbeStatus.DEAD


# ---------------------------------------------------------------------------
# 17. classify — TAK gets HTML, generic gets image → DEGRADED
# ---------------------------------------------------------------------------


class TestClassifyDegraded:
    def test_tak_html_generic_image_returns_degraded(self):
        tak = (200, None, False, 500)  # 200 but not image
        generic = (200, None, True, 15000)
        assert classify(tak, generic) == ProbeStatus.DEGRADED


class TestClassifyEdgeCases:
    def test_tak_404_generic_ok_is_dead_not_blocked(self):
        """404 is not a block — it's a different failure. Only 403/429 = BLOCKED."""
        tak = (404, "HTTP 404", False, 0)
        generic = (200, None, True, 15000)
        # Per spec: BLOCKED requires 403 or 429. 404 falls through to DEAD.
        assert classify(tak, generic) == ProbeStatus.DEAD

    def test_tak_ok_generic_fail_is_dead(self):
        """Spec requires BOTH user-agents to return 200+image for HEALTHY."""
        tak = (200, None, True, 15000)
        generic = (500, "HTTP 500", False, 0)
        # TAK ok + generic fail doesn't match any spec matrix row → DEAD
        assert classify(tak, generic) == ProbeStatus.DEAD

    def test_both_200_but_both_html_is_dead(self):
        """Both return 200 but neither returns an image → server broken."""
        tak = (200, None, False, 500)
        generic = (200, None, False, 500)
        assert classify(tak, generic) == ProbeStatus.DEAD


# ---------------------------------------------------------------------------
# 18. probe_source — healthy TMS
# ---------------------------------------------------------------------------


class TestProbeSourceHealthy:
    @responses.activate
    def test_healthy_tms_returns_healthy_result(self):
        # Mock all tile URLs from example.com with a regex pattern
        responses.add(
            responses.GET,
            re.compile(r"https://tiles\.example\.com/\d+/\d+/\d+\.png"),
            body=b"\x89PNG\r\n",
            status=200,
            content_type="image/png",
        )

        root = _xml(TMS_XYZ_XML)
        result = probe_source(root, Path("Test/test.xml"))

        assert isinstance(result, ProbeResult)
        assert result.status == ProbeStatus.HEALTHY
        assert result.map_name == "Test TMS"
        assert result.filepath == Path("Test/test.xml")
        assert result.tak_status_code == 200
        assert result.tak_error is None
        assert result.generic_status_code == 200
        assert result.generic_error is None


# ---------------------------------------------------------------------------
# 19. probe_source — multi-zoom fallback
# ---------------------------------------------------------------------------


class TestProbeSourceMultiZoomFallback:
    @responses.activate
    def test_first_url_404_later_url_200_returns_healthy(self):
        # First URL (minZoom=2 at 0,0) -> 404, remaining URLs -> 200
        responses.add(
            responses.GET,
            "https://tiles.example.com/2/0/0.png",
            status=404,
            body=b"Not Found",
        )
        responses.add(
            responses.GET,
            "https://tiles.example.com/2/0/0.png",
            status=404,
            body=b"Not Found",
        )
        # All other URLs return healthy tiles
        responses.add(
            responses.GET,
            re.compile(r"https://tiles\.example\.com/\d+/\d+/\d+\.png"),
            body=b"\x89PNG\r\n",
            status=200,
            content_type="image/png",
        )

        root = _xml(TMS_XYZ_XML)
        result = probe_source(root, Path("Test/test.xml"))
        assert result.status == ProbeStatus.HEALTHY


# ---------------------------------------------------------------------------
# 20. probe_source — dead server
# ---------------------------------------------------------------------------


class TestProbeSourceDead:
    @responses.activate
    def test_all_urls_fail_returns_dead(self):
        # All tile URLs return 500
        responses.add(
            responses.GET,
            re.compile(r"https://tiles\.example\.com/\d+/\d+/\d+\.png"),
            status=500,
            body=b"Error",
        )

        root = _xml(TMS_XYZ_XML)
        result = probe_source(root, Path("Test/test.xml"))
        assert result.status == ProbeStatus.DEAD
        assert result.tak_status_code is not None or result.tak_error is not None


# ---------------------------------------------------------------------------
# 21. SMOKE_SOURCES constant
# ---------------------------------------------------------------------------


class TestSmokeSources:
    def test_smoke_sources_contains_expected_files(self):
        assert "Google/google_hybrid.xml" in SMOKE_SOURCES
        assert "ESRI/esri_clarity.xml" in SMOKE_SOURCES
        assert "Bing/Bing_Satellite.xml" in SMOKE_SOURCES

    def test_smoke_sources_has_exactly_three_entries(self):
        assert len(SMOKE_SOURCES) == 3


# ---------------------------------------------------------------------------
# 22. probe_smoke — filters to only SMOKE_SOURCES
# ---------------------------------------------------------------------------


class TestProbeSmoke:
    @responses.activate
    def test_probes_only_smoke_sources(self, tmp_path):
        """probe_smoke should only probe files listed in SMOKE_SOURCES."""
        # Create directory structure with smoke + non-smoke XML files
        google_dir = tmp_path / "Google"
        google_dir.mkdir()
        esri_dir = tmp_path / "ESRI"
        esri_dir.mkdir()
        bing_dir = tmp_path / "Bing"
        bing_dir.mkdir()
        other_dir = tmp_path / "Other"
        other_dir.mkdir()

        tms_xml = """\
<customMapSource>
    <name>Test Source</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>"""

        (google_dir / "google_hybrid.xml").write_text(tms_xml)
        (esri_dir / "esri_clarity.xml").write_text(tms_xml)
        (bing_dir / "Bing_Satellite.xml").write_text(tms_xml)
        (other_dir / "some_other_map.xml").write_text(tms_xml)

        # Mock all tile URLs from example.com
        responses.add(
            responses.GET,
            re.compile(r"https://tiles\.example\.com/\d+/\d+/\d+\.png"),
            body=b"\x89PNG\r\n",
            status=200,
            content_type="image/png",
        )

        results = probe_smoke(tmp_path)

        # Should probe exactly the 3 smoke sources, not the "other" one
        assert len(results) == 3
        probed_files = {r.filepath.name for r in results}
        assert "google_hybrid.xml" in probed_files
        assert "esri_clarity.xml" in probed_files
        assert "Bing_Satellite.xml" in probed_files
        assert "some_other_map.xml" not in probed_files

    @responses.activate
    def test_missing_smoke_source_is_skipped(self, tmp_path):
        """If a smoke source file doesn't exist, it should be skipped."""
        # Only create one of the three smoke sources
        google_dir = tmp_path / "Google"
        google_dir.mkdir()

        tms_xml = """\
<customMapSource>
    <name>Google Hybrid</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>"""

        (google_dir / "google_hybrid.xml").write_text(tms_xml)

        responses.add(
            responses.GET,
            re.compile(r"https://tiles\.example\.com/\d+/\d+/\d+\.png"),
            body=b"\x89PNG\r\n",
            status=200,
            content_type="image/png",
        )

        results = probe_smoke(tmp_path)
        assert len(results) == 1
        assert results[0].filepath.name == "google_hybrid.xml"


# ---------------------------------------------------------------------------
# 23. probe_all with smoke_only flag
# ---------------------------------------------------------------------------


class TestProbeAllSmokeFlag:
    @responses.activate
    def test_probe_all_smoke_only_filters_sources(self, tmp_path):
        """probe_all(smoke_only=True) should behave like probe_smoke."""
        google_dir = tmp_path / "Google"
        google_dir.mkdir()
        other_dir = tmp_path / "Other"
        other_dir.mkdir()

        tms_xml = """\
<customMapSource>
    <name>Test Source</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>"""

        (google_dir / "google_hybrid.xml").write_text(tms_xml)
        (other_dir / "other_map.xml").write_text(tms_xml)

        responses.add(
            responses.GET,
            re.compile(r"https://tiles\.example\.com/\d+/\d+/\d+\.png"),
            body=b"\x89PNG\r\n",
            status=200,
            content_type="image/png",
        )

        results = probe_all(tmp_path, smoke_only=True)
        assert len(results) == 1
        assert results[0].filepath.name == "google_hybrid.xml"
