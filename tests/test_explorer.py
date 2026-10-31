"""Map explorer data: every map turned into what the live web map needs.

The explorer draws each map with Leaflet in the browser, so the tile URL rules
must match ATAK's (atak_source) and every map needs a region, a credit and a
place where it has data.
"""

import json
from pathlib import Path

from mapvalidator.explorer import (
    build_explorer_data,
    credit_for,
    health_js,
    leaf_specs,
    region_for,
)
from mapvalidator.atak_source import parse_source


def _map(root: Path, rel: str, xml: str) -> Path:
    f = root / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(xml)
    return f


TMS = """<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>{name}</name>
    <minZoom>1</minZoom>
    <maxZoom>17</maxZoom>
    <tileType>png</tileType>
    <url>https://{{$serverpart}}.t.example/{{$z}}/{{$x}}/{{$y}}.png</url>
    <serverParts>a b c</serverParts>
</customMapSource>
"""

QUADKEY = """<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Quad</name>
    <maxZoom>19</maxZoom>
    <url>https://q.example/tiles/r{$q}.png</url>
    <invertYCoordinate>true</invertYCoordinate>
</customMapSource>
"""

WMS = """<?xml version="1.0" encoding="UTF-8"?>
<customWmsMapSource>
    <name>+ Flood</name>
    <minZoom>5</minZoom>
    <maxZoom>19</maxZoom>
    <tileType>PNG</tileType>
    <version>1.3.0</version>
    <layers>12</layers>
    <url>https://wms.example/WMSServer?map=a&amp;TRANSPARENT=TRUE</url>
    <additionalparameters>&amp;dpi=96</additionalparameters>
</customWmsMapSource>
"""

MULTI = """<?xml version="1.0" encoding="UTF-8"?>
<customMultiLayerMapSource>
    <name>Sat + Labels</name>
    <layers>
        <customMapSource><name>Sat</name><maxZoom>18</maxZoom><url>https://s.example/{$z}/{$x}/{$y}.jpg</url></customMapSource>
        <customMapSource><name>Labels</name><maxZoom>16</maxZoom><url>https://l.example/{$z}/{$x}/{$y}.png</url></customMapSource>
    </layers>
</customMultiLayerMapSource>
"""


class TestLeafSpecs:
    def test_tms_placeholders_become_leaflet_template(self, tmp_path):
        (spec,) = leaf_specs(
            parse_source(_map(tmp_path, "x/a.xml", TMS.format(name="A")))
        )
        assert spec["kind"] == "tms"
        assert spec["url"] == "https://{s}.t.example/{z}/{x}/{y}.png"
        assert spec["subdomains"] == ["a", "b", "c"]
        assert (spec["min"], spec["max"], spec["tms"], spec["quadkey"]) == (
            1,
            17,
            False,
            False,
        )

    def test_quadkey_and_inverted_y(self, tmp_path):
        (spec,) = leaf_specs(parse_source(_map(tmp_path, "x/q.xml", QUADKEY)))
        assert spec["url"] == "https://q.example/tiles/r{q}.png"
        assert spec["quadkey"] is True and spec["tms"] is True

    def test_wms_splits_base_and_keeps_extra_parameters(self, tmp_path):
        (spec,) = leaf_specs(
            parse_source(_map(tmp_path, "maps/overlays/grg_f.xml", WMS))
        )
        assert spec["kind"] == "wms"
        assert spec["base"] == "https://wms.example/WMSServer"
        assert (spec["layers"], spec["version"], spec["format"]) == (
            "12",
            "1.3.0",
            "image/png",
        )
        assert spec["extra"] == {"map": "a", "TRANSPARENT": "TRUE", "dpi": "96"}

    def test_multi_layer_flattens_to_its_layers(self, tmp_path):
        specs = leaf_specs(parse_source(_map(tmp_path, "x/m.xml", MULTI)))
        assert [s["url"] for s in specs] == [
            "https://s.example/{z}/{x}/{y}.jpg",
            "https://l.example/{z}/{x}/{y}.png",
        ]


class TestRegionAndCredit:
    def test_region_from_description(self):
        assert region_for("USGS topographic basemap — United States.") == "US"
        assert region_for("Ordnance Survey Road — Great Britain.") == "UK"
        assert (
            region_for("basemap.de raster — official German government basemap.")
            == "DE"
        )
        assert region_for("BLM public-lands ownership overlay") == "US"
        assert region_for("Google satellite imagery — global.") == "Global"

    def test_credit_by_folder_and_overlay_prefix(self):
        assert (
            credit_for(Path("maps/base/esri/esri_topo.xml"))
            == "© Esri and its data providers"
        )
        assert (
            credit_for(Path("maps/overlays/grg_fema_flood.xml"))
            == "FEMA National Flood Hazard Layer"
        )
        assert credit_for(Path("unknown/thing.xml")) == ""


class TestBuildExplorerData:
    def test_one_entry_per_map_with_what_the_page_needs(self, tmp_path):
        _map(
            tmp_path, "maps/base/google/google_road.xml", TMS.format(name="Google Road")
        )
        _map(tmp_path, "maps/overlays/grg_fema_flood.xml", WMS)
        desc = {
            "google-google-road": {"category": "Street", "text": "Road map — global."},
            "grg-grg-fema-flood": {
                "category": "Overlay",
                "text": "Flood zones, United States.",
                "test_point": [29.76, -95.37],
            },
        }
        data = {m["slug"]: m for m in build_explorer_data(tmp_path, desc)}
        road, fema = data["google-google-road"], data["grg-grg-fema-flood"]
        assert (road["name"], road["category"], road["region"], road["overlay"]) == (
            "Google Road",
            "Street",
            "Global",
            False,
        )
        assert road["credit"] == "© Google"
        assert road["importUri"].startswith("tak://com.atakmap.app/import?url=")
        # the XML itself, for manual installs and for adding an API key
        assert (
            road["xmlUrl"]
            == "https://joshuafuller.github.io/ATAK-Maps/sources/google/google_road.xml"
        )
        assert (
            road["sourceUrl"].endswith("/maps/base/google/google_road.xml")
            and "github" in road["sourceUrl"]
        )
        assert road["point"] == [40.7128, -74.006]  # harness default test point
        assert (fema["overlay"], fema["region"], fema["point"]) == (
            True,
            "US",
            [29.76, -95.37],
        )

    def test_api_key_maps_are_flagged(self, tmp_path):
        _map(
            tmp_path,
            "uk-os/uk_os_road.xml",
            TMS.format(name="UK OS Road").replace(".png<", ".png?key=API_KEY_HERE<"),
        )
        (entry,) = build_explorer_data(tmp_path, {})
        assert entry["needsKey"] is True

    def test_live_point_overrides_test_point(self, tmp_path):
        _map(tmp_path, "maps/overlays/grg_fema_flood.xml", WMS)
        (entry,) = build_explorer_data(
            tmp_path,
            {},
            live_points={"grg-grg-fema-flood": lambda: ([51.2, -121.7], 10)},
        )
        assert (entry["point"], entry["zoom"]) == ([51.2, -121.7], 10)

    def test_failed_live_lookup_keeps_test_point(self, tmp_path):
        _map(tmp_path, "maps/overlays/grg_fema_flood.xml", WMS)
        (entry,) = build_explorer_data(
            tmp_path, {}, live_points={"grg-grg-fema-flood": lambda: None}
        )
        assert entry["point"] == [40.7128, -74.006] and entry["zoom"] is None


class TestHealthJs:
    def test_wraps_harness_json_for_the_page(self, tmp_path):
        f = tmp_path / "map-health.json"
        f.write_text(
            json.dumps({"x-m": {"status": "ok", "checked": "t", "problem": ""}})
        )
        js = health_js(f)
        assert js.startswith("window.ATAK_HEALTH = ") and js.rstrip().endswith(";")
        assert (
            json.loads(js.split("=", 1)[1].strip().rstrip(";"))["x-m"]["status"] == "ok"
        )

    def test_missing_or_bad_file_gives_empty_health(self, tmp_path):
        assert health_js(tmp_path / "nope.json").strip() == "window.ATAK_HEALTH = {};"
        bad = tmp_path / "bad.json"
        bad.write_text("not json")
        assert health_js(bad).strip() == "window.ATAK_HEALTH = {};"
