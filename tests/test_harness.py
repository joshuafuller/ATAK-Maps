"""Harness checks, driven by a fake network (the only external dependency).

Each map is fetched the way ATAK fetches it (atak_source.tile_url, User-Agent
"TAK") at minZoom, maxZoom and maxZoom + 1, and every response is classified
by tile_content.classify_tile.
"""

import io
import re
from pathlib import Path

from PIL import Image

from mapvalidator.harness import (
    Finding,
    Response,
    check_source,
    format_report,
    health_report,
    run_harness,
)

FIXTURES = Path(__file__).parent / "fixtures" / "tiles"
REAL = (FIXTURES / "usgs_topo_real.jpg").read_bytes()
PLACEHOLDER = (FIXTURES / "esri_not_available.jpg").read_bytes()


def _png(color) -> bytes:
    buf = io.BytesIO()
    Image.new("RGBA", (256, 256), color).save(buf, "PNG")
    return buf.getvalue()


def _overlay_png() -> bytes:
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    img.paste((0, 90, 200, 255), (0, 0, 64, 256))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


EMPTY = _png((0, 0, 0, 0))


class FakeNet:
    """Answers by zoom level; records every (url, user_agent) request."""

    def __init__(self, by_zoom=None, default=REAL, browser=None, error=None):
        self.by_zoom = by_zoom or {}
        self.default = default
        self.browser = browser
        self.error = error
        self.calls = []

    def __call__(self, url, user_agent):
        self.calls.append((url, user_agent))
        if self.error:
            return Response(None, None, b"", self.error)
        if user_agent != "TAK" and self.browser is not None:
            return Response(200, "image/png", self.browser, None)
        z = int(re.search(r"/(\d+)/\d+/\d+\.png", url).group(1))
        value = self.by_zoom.get(z, self.default)
        if isinstance(value, int):
            return Response(value, "text/html", b"<html>error</html>", None)
        return Response(200, "image/png", value, None)


def _map(
    tmp_path,
    folder,
    name,
    min_zoom=3,
    max_zoom=12,
    url="https://t.example/{$z}/{$x}/{$y}.png",
):
    d = tmp_path / folder
    d.mkdir(parents=True, exist_ok=True)
    f = d / "m.xml"
    f.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>{name}</name>
    <minZoom>{min_zoom}</minZoom>
    <maxZoom>{max_zoom}</maxZoom>
    <tileType>png</tileType>
    <url>{url}</url>
</customMapSource>
"""
    )
    return f


def _levels(findings, level):
    return [f for f in findings if f.level == level]


class TestBaseMaps:
    def test_healthy_map_has_no_errors(self, tmp_path):
        findings = check_source(
            _map(tmp_path, "esri", "Esri Topo"), tmp_path, FakeNet()
        )
        assert _levels(findings, "error") == []

    def test_placeholder_at_max_zoom_means_max_zoom_too_high(self, tmp_path):
        net = FakeNet(by_zoom={12: PLACEHOLDER, 13: PLACEHOLDER})
        errors = _levels(
            check_source(_map(tmp_path, "esri", "Esri Topo"), tmp_path, net), "error"
        )
        assert len(errors) == 1
        assert "maxZoom" in errors[0].message and "placeholder" in errors[0].message

    def test_http_error_at_min_zoom(self, tmp_path):
        net = FakeNet(by_zoom={3: 404})
        errors = _levels(
            check_source(_map(tmp_path, "esri", "Esri Topo"), tmp_path, net), "error"
        )
        assert any("z3" in e.message and "404" in e.message for e in errors)

    def test_blank_tile_at_max_zoom_warns(self, tmp_path):
        # one colour at high zoom can be real (water, a roof) or a server's
        # "no data" fill (Canada CBMT above z19 is solid black) -> warn
        net = FakeNet(by_zoom={12: _png((0, 0, 0, 255))})
        findings = check_source(
            _map(tmp_path, "ca-nrcan", "CA Base Map"), tmp_path, net
        )
        assert _levels(findings, "error") == []
        assert any("blank" in w.message for w in _levels(findings, "warn"))

    def test_blank_tile_at_min_zoom_is_an_error(self, tmp_path):
        net = FakeNet(by_zoom={3: _png((0, 0, 0, 255))})
        errors = _levels(
            check_source(_map(tmp_path, "ca-nrcan", "CA Base Map"), tmp_path, net),
            "error",
        )
        assert any("blank" in e.message for e in errors)

    def test_real_data_above_max_zoom_is_reported(self, tmp_path):
        infos = _levels(
            check_source(_map(tmp_path, "usgs", "USGS Topo"), tmp_path, FakeNet()),
            "info",
        )
        assert any("z13" in i.message for i in infos)

    def test_no_report_when_server_stops_at_max_zoom(self, tmp_path):
        net = FakeNet(by_zoom={13: 404})
        findings = check_source(_map(tmp_path, "usgs", "USGS Topo"), tmp_path, net)
        assert findings == []

    def test_fetches_with_atak_user_agent(self, tmp_path):
        net = FakeNet()
        check_source(_map(tmp_path, "esri", "Esri Topo"), tmp_path, net)
        assert {ua for _, ua in net.calls} == {"TAK"}

    def test_blocked_for_tak_but_not_browser(self, tmp_path):
        net = FakeNet(default=(FIXTURES / "osm_blocked.png").read_bytes(), browser=REAL)
        errors = _levels(
            check_source(_map(tmp_path, "osm", "OSM Road"), tmp_path, net), "error"
        )
        assert any("User-Agent" in e.message for e in errors)

    def test_connection_error_is_reported(self, tmp_path):
        net = FakeNet(error="SSL: certificate verify failed")
        errors = _levels(
            check_source(_map(tmp_path, "bing", "Bing Road"), tmp_path, net), "error"
        )
        assert errors and "certificate verify failed" in errors[0].message

    def test_api_key_placeholder_skips_network(self, tmp_path):
        net = FakeNet()
        f = _map(
            tmp_path,
            "uk-os",
            "UK OS Road",
            url="https://api.example/{$z}/{$x}/{$y}.png?key=API_KEY_HERE",
        )
        findings = check_source(f, tmp_path, net)
        assert net.calls == []
        assert [x.level for x in findings] == ["info"]


class TestTestPoint:
    def test_default_point_is_new_york(self, tmp_path):
        net = FakeNet()
        check_source(
            _map(tmp_path, "esri", "Esri Topo", min_zoom=10, max_zoom=10), tmp_path, net
        )
        assert net.calls[0][0] == "https://t.example/10/301/385.png"

    def test_point_from_descriptions(self, tmp_path):
        net = FakeNet()
        f = _map(tmp_path, "de-basemap", "DE Basemap Color", min_zoom=10, max_zoom=10)
        (tmp_path / "maps").mkdir(exist_ok=True)
        (tmp_path / "maps" / "descriptions.yml").write_text(
            "de-basemap-m:\n  category: Street\n  test_point: [52.52, 13.405]\n"
        )
        check_source(f, tmp_path, net)
        # Berlin z10: x = (193.405 / 360) * 1024 = 550, y = 335
        assert net.calls[0][0] == "https://t.example/10/550/335.png"


class TestOverlays:
    def test_overlay_name_must_start_with_plus(self, tmp_path):
        net = FakeNet(default=_overlay_png())
        errors = _levels(
            check_source(
                _map(tmp_path, "maps/overlays", "Google Roads"), tmp_path, net
            ),
            "error",
        )
        assert any("+ " in e.message for e in errors)

    def test_base_map_name_must_not_start_with_plus(self, tmp_path):
        errors = _levels(
            check_source(
                _map(tmp_path, "google", "+ Google Road"), tmp_path, FakeNet()
            ),
            "error",
        )
        assert any("+ " in e.message for e in errors)

    def test_opaque_overlay_is_an_error(self, tmp_path):
        errors = _levels(
            check_source(
                _map(tmp_path, "maps/overlays", "+ Relief"), tmp_path, FakeNet()
            ),
            "error",
        )
        assert any("opaque" in e.message for e in errors)

    def test_empty_overlay_tile_is_fine(self, tmp_path):
        net = FakeNet(default=EMPTY)
        assert (
            _levels(
                check_source(
                    _map(tmp_path, "maps/overlays", "+ FEMA Flood"), tmp_path, net
                ),
                "error",
            )
            == []
        )


class TestNames:
    def test_long_name_warns(self, tmp_path):
        warns = _levels(
            check_source(
                _map(tmp_path, "esri", "Esri World Topographic Map"),
                tmp_path,
                FakeNet(),
            ),
            "warn",
        )
        assert any("characters" in w.message for w in warns)


class TestWms:
    def test_unsupported_wms_tile_type(self, tmp_path):
        d = tmp_path / "x"
        d.mkdir()
        f = d / "w.xml"
        f.write_text(
            """<customWmsMapSource><name>X Map</name><maxZoom>5</maxZoom>
<tileType>jpeg</tileType><layers>1</layers><url>https://w.example/wms?</url></customWmsMapSource>"""
        )
        errors = _levels(check_source(f, tmp_path, FakeNet()), "error")
        assert any("format=null" in e.message for e in errors)


class TestRunHarness:
    def test_exit_code_and_report(self, tmp_path):
        _map(tmp_path, "esri", "Esri Topo")
        bad = tmp_path / "maps" / "overlays"
        bad.mkdir(parents=True)
        (bad / "roads.xml").write_text(
            (tmp_path / "esri" / "m.xml").read_text().replace("Esri Topo", "Roads")
        )
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "ignored.xml").write_text("<not-a-map/>")

        results = run_harness(tmp_path, FakeNet(default=_overlay_png()))
        report, exit_code = format_report(results)

        assert [p.as_posix() for p in results] == [
            "esri/m.xml",
            "maps/overlays/roads.xml",
        ]
        assert exit_code == 1
        assert "maps/overlays/roads.xml" in report and "ERROR" in report

    def test_clean_run_exits_zero(self, tmp_path):
        _map(tmp_path, "esri", "Esri Topo")
        report, exit_code = format_report(
            run_harness(tmp_path, FakeNet(by_zoom={13: 404}))
        )
        assert exit_code == 0
        assert "1 maps, 0 errors" in report

    def test_only_checks_named_files(self, tmp_path):
        _map(tmp_path, "esri", "Esri Topo")
        _map(tmp_path, "usgs", "USGS Topo")
        net = FakeNet(by_zoom={13: 404})
        results = run_harness(tmp_path, net, only=[tmp_path / "usgs" / "m.xml"])
        assert [p.as_posix() for p in results] == ["usgs/m.xml"]
        assert all("/t.example/" in url for url, _ in net.calls)


def _multi(tmp_path, name, layers_xml, folder="blm"):
    d = tmp_path / folder
    d.mkdir(parents=True, exist_ok=True)
    f = d / "combo.xml"
    f.write_text(
        f"""<customMultiLayerMapSource><name>{name}</name><layers>{layers_xml}</layers>
</customMultiLayerMapSource>"""
    )
    return f


def _child(host, max_zoom=12):
    return (
        f"<customMapSource><name>{host}</name><minZoom>3</minZoom><maxZoom>{max_zoom}</maxZoom>"
        f"<url>https://{host}.example/{{$z}}/{{$x}}/{{$y}}.png</url></customMapSource>"
    )


class HostNet(FakeNet):
    """Answers by host name: {host: body}."""

    def __init__(self, by_host):
        super().__init__()
        self.by_host = by_host

    def __call__(self, url, user_agent):
        self.calls.append((url, user_agent))
        host = url.split("/")[2].split(".")[0]
        z = int(re.search(r"/(\d+)/\d+/\d+\.png", url).group(1))
        if z == 13:
            return Response(404, "text/html", b"<html/>", None)
        return Response(200, "image/png", self.by_host[host], None)


class TestMultiLayer:
    def test_transparent_child_over_real_base_is_fine(self, tmp_path):
        f = _multi(tmp_path, "BLM Sat + Ownership", _child("sat") + _child("sma"))
        net = HostNet({"sat": REAL, "sma": EMPTY})
        assert _levels(check_source(f, tmp_path, net), "error") == []

    def test_composite_with_no_data_is_an_error(self, tmp_path):
        f = _multi(tmp_path, "BLM Sat + Ownership", _child("sat") + _child("sma"))
        net = HostNet({"sat": EMPTY, "sma": EMPTY})
        errors = _levels(check_source(f, tmp_path, net), "error")
        assert any("no layer" in e.message for e in errors)

    def test_nested_composite_is_checked(self, tmp_path):
        inner = (
            "<customMultiLayerMapSource><name>Inner</name>"
            f"<layers>{_child('b')}</layers></customMultiLayerMapSource>"
        )
        f = _multi(tmp_path, "Nested", _child("a") + inner)
        net = HostNet({"a": REAL, "b": REAL})
        findings = check_source(f, tmp_path, net)
        assert _levels(findings, "error") == []
        assert any(url.startswith("https://b.example/") for url, _ in net.calls)


class TestSemiTransparentOverlay:
    def test_semi_transparent_overlay_passes_opacity_rule(self, tmp_path):
        img = Image.new("RGBA", (256, 256), (200, 30, 30, 128))
        img.paste((30, 30, 200, 128), (0, 0, 64, 256))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        net = FakeNet(default=buf.getvalue())
        assert (
            _levels(
                check_source(_map(tmp_path, "maps/overlays", "+ Tint"), tmp_path, net),
                "error",
            )
            == []
        )


class TestHealthReport:
    """Per-map status the site's map explorer shows ("Working in ATAK" / problem)."""

    CHECKED = "2026-10-30T12:00:00+00:00"

    def test_status_per_map_keyed_by_catalog_slug(self):
        results = {
            Path("esri/esri_topo.xml"): [],
            Path("bing/bing_road.xml"): [Finding("warn", "maxZoom z20: blank tile")],
            Path("GRG/grg_fema_flood.xml"): [
                Finding("info", "server has real tiles at z20"),
                Finding("error", "minZoom z5: HTTP 500"),
            ],
        }
        report = health_report(results, self.CHECKED)
        assert report["esri-esri-topo"] == {
            "status": "ok",
            "checked": self.CHECKED,
            "problem": "",
        }
        assert report["bing-bing-road"]["status"] == "warn"
        assert report["grg-grg-fema-flood"]["status"] == "fail"

    def test_problem_is_the_first_error_not_info(self):
        results = {
            Path("x/m.xml"): [
                Finding("info", "server has real tiles at z20"),
                Finding("warn", "name is long"),
                Finding("error", "minZoom z1: HTTP 404"),
            ]
        }
        assert (
            health_report(results, self.CHECKED)["x-m"]["problem"]
            == "minZoom z1: HTTP 404"
        )

    def test_info_only_is_ok(self):
        results = {
            Path("x/m.xml"): [Finding("info", "needs an API key; tile checks skipped")]
        }
        assert health_report(results, self.CHECKED)["x-m"]["status"] == "ok"
