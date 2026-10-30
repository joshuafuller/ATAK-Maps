"""ATAK URL fidelity: parse and build tile URLs exactly as ATAK 5.x does.

Expected values are worked by hand from the ATAK source (takkernel):
MobacMapSourceFactory, CustomMobacMapSource.getUrl/getQuadKey/loadTile and
CustomWmsMobacMapSource.getUrl/fixupURL.
"""

from pathlib import Path

import pytest

from mapvalidator.atak_source import java_double, parse_source, tile_for_point, tile_url


def _write(tmp_path: Path, xml: str) -> Path:
    f = tmp_path / "src.xml"
    f.write_text(xml)
    return f


TMS = """<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Test TMS</name>
    <minZoom>2</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://{$serverpart}.t.example/{$z}/{$x}/{$y}.png?q={$q}</url>
    <serverParts>a b c</serverParts>
</customMapSource>
"""


class TestTmsUrls:
    def test_placeholders_and_quadkey(self, tmp_path):
        src = parse_source(_write(tmp_path, TMS))
        # quadkey z3 x3 y5 = "213" (bit 4: y -> 2; bit 2: x -> 1; bit 1: x+y -> 3)
        assert tile_url(src, 3, 3, 5) == "https://a.t.example/3/3/5.png?q=213"

    def test_server_parts_rotate_like_atak(self, tmp_path):
        src = parse_source(_write(tmp_path, TMS))
        hosts = [tile_url(src, 3, 3, 5, server_part=i).split(".")[0] for i in range(4)]
        assert hosts == ["https://a", "https://b", "https://c", "https://a"]

    def test_invert_y(self, tmp_path):
        xml = TMS.replace("</serverParts>", "</serverParts>\n<invertYCoordinate>true</invertYCoordinate>")
        src = parse_source(_write(tmp_path, xml))
        # z3: y = (2^3 - 1) - 5 = 2
        assert tile_url(src, 3, 3, 5).startswith("https://a.t.example/3/3/2.png")

    def test_url_is_html_unescaped_after_xml_parsing(self, tmp_path):
        # XML parsing turns &amp;amp; into &amp;; ATAK then calls unescapeHtml -> &
        xml = TMS.replace("?q={$q}", "?a=1&amp;amp;b=2")
        src = parse_source(_write(tmp_path, xml))
        assert tile_url(src, 3, 3, 5) == "https://a.t.example/3/3/5.png?a=1&b=2"

    def test_empty_server_parts_leaves_placeholder(self, tmp_path):
        xml = TMS.replace("<serverParts>a b c</serverParts>", "<serverParts></serverParts>")
        src = parse_source(_write(tmp_path, xml))
        assert tile_url(src, 3, 3, 5).startswith("https://{$serverpart}.t.example/")

    def test_zoom_range(self, tmp_path):
        src = parse_source(_write(tmp_path, TMS))
        assert (src.min_zoom, src.max_zoom) == (2, 18)


WMS = """<?xml version="1.0" encoding="UTF-8"?>
<customWmsMapSource>
    <name>Test WMS</name>
    <maxZoom>19</maxZoom>
    <tileType>{tile_type}</tileType>
    <version>{version}</version>
    <layers>12</layers>
    <url><![CDATA[https://h.example/WMSServer?]]></url>
    {extra}
</customWmsMapSource>
"""


def _wms(tmp_path, tile_type="PNG", version="1.3.0", extra=""):
    return parse_source(_write(tmp_path, WMS.format(tile_type=tile_type, version=version, extra=extra)))


class TestWmsUrls:
    def test_default_srid_4326_with_v13_uses_crs84(self, tmp_path):
        src = _wms(tmp_path, extra="<aditionalparameters><![CDATA[&TRANSPARENT=TRUE]]></aditionalparameters>")
        # 4326 grid is 2x1: z0 tile (0,0) covers lon -180..0, lat -90..90
        assert tile_url(src, 0, 0, 0) == (
            "https://h.example/WMSServer?service=WMS&request=GetMap&layers=12&crs=CRS:84"
            "&format=image/png&width=256&height=256&version=1.3.0&styles="
            "&TRANSPARENT=TRUE&bbox=-180.0,-90.0,0.0,90.0"
        )

    def test_v111_uses_srs_epsg(self, tmp_path):
        url = tile_url(_wms(tmp_path, version="1.1.1"), 0, 1, 0)
        assert "&srs=EPSG:4326&" in url
        assert url.endswith("&bbox=0.0,-90.0,180.0,90.0")

    def test_atak_always_sends_styles(self, tmp_path):
        # The FEMA bug: STYLES in additional parameters duplicates ATAK's own styles=
        src = _wms(tmp_path, extra="<aditionalparameters><![CDATA[&STYLES=default]]></aditionalparameters>")
        assert tile_url(src, 0, 0, 0).lower().count("styles=") == 2

    def test_styles_element_is_used(self, tmp_path):
        assert "&styles=boundaries&" in tile_url(_wms(tmp_path, extra="<styles>boundaries</styles>"), 0, 0, 0)

    def test_lowercase_tiletype_maps_to_mime(self, tmp_path):
        assert "&format=image/jpeg&" in tile_url(_wms(tmp_path, tile_type="jpg"), 0, 0, 0)

    def test_unknown_tiletype_sends_format_null(self, tmp_path):
        # ATAK only maps JPG and PNG; anything else concatenates a null
        assert "&format=null&" in tile_url(_wms(tmp_path, tile_type="jpeg"), 0, 0, 0)

    def test_web_mercator_bbox(self, tmp_path):
        src = _wms(tmp_path, version="1.1.1", extra="<coordinatesystem>EPSG:3857</coordinatesystem>")
        url = tile_url(src, 1, 1, 0)  # north-east quarter of the world
        assert "&srs=EPSG:3857&" in url
        west, south, east, north = (float(v) for v in url.split("&bbox=")[1].split(","))
        assert west == 0.0 and south == pytest.approx(0.0, abs=1e-6)
        assert east == pytest.approx(20037508.342789244) and north == pytest.approx(20037508.342789244)

    def test_url_without_query_gets_question_mark(self, tmp_path):
        xml = WMS.format(tile_type="PNG", version="1.1.1", extra="").replace(
            "WMSServer?]]>", "WMSServer]]>")
        assert tile_url(parse_source(_write(tmp_path, xml)), 0, 0, 0).startswith(
            "https://h.example/WMSServer?service=WMS&")

    def test_url_with_query_gets_ampersand(self, tmp_path):
        xml = WMS.format(tile_type="PNG", version="1.1.1", extra="").replace(
            "WMSServer?]]>", "WMSServer?map=x]]>")
        assert tile_url(parse_source(_write(tmp_path, xml)), 0, 0, 0).startswith(
            "https://h.example/WMSServer?map=x&service=WMS&")


class TestJavaDouble:
    @pytest.mark.parametrize("value, text", [
        (0.0, "0.0"),
        (-180.0, "-180.0"),
        (1234.5, "1234.5"),
        (9999999.0, "9999999.0"),
        (-20037508.342789244, "-2.0037508342789244E7"),
        (10000000.0, "1.0E7"),
        (0.0001, "1.0E-4"),
    ])
    def test_matches_java_string_valueof(self, value, text):
        assert java_double(value) == text


class TestTileForPoint:
    def test_web_mercator_nyc(self, tmp_path):
        src = parse_source(_write(tmp_path, TMS))
        assert tile_for_point(src, 40.7128, -74.0060, 10) == (301, 385)

    def test_wgs84_grid_is_two_tiles_wide(self, tmp_path):
        src = _wms(tmp_path)  # default srid 4326
        # z2: tile = 45 deg; lon -95 -> (85 / 45) = 1, lat 29.75 -> (60.25 / 45) = 1
        assert tile_for_point(src, 29.75, -95.0, 2) == (1, 1)


class TestMultiLayer:
    def test_children_are_parsed(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<customMultiLayerMapSource>
    <name>Combo</name>
    <layers>
        <customMapSource><name>A</name><maxZoom>10</maxZoom><url>https://a/{$z}/{$x}/{$y}</url></customMapSource>
        <customMapSource><name>B</name><maxZoom>12</maxZoom><url>https://b/{$z}/{$x}/{$y}</url></customMapSource>
    </layers>
</customMultiLayerMapSource>
"""
        src = parse_source(_write(tmp_path, xml))
        assert src.kind == "multi"
        assert [tile_url(c, 1, 0, 1) for c in src.children] == ["https://a/1/0/1", "https://b/1/0/1"]
