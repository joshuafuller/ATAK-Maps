"""Tile content checks: is a 200 response real map data?

Fixtures in tests/fixtures/tiles are real server responses:
- usgs_topo_real.jpg   USGSTopo z16 over New York (real data)
- esri_not_available.jpg  Esri NatGeo z17: grey "Map data not yet available"
- osm_blocked.png      tile.openstreetmap.org to User-Agent "TAK": "Access blocked"
- bing_no_imagery.png  Bing aerial z22: "no imagery" placeholder
- wms_exception.txt    FEMA WMS with a duplicate STYLES parameter
"""

import io
from pathlib import Path

import pytest
from PIL import Image

from mapvalidator.tile_content import classify_tile

FIXTURES = Path(__file__).parent / "fixtures" / "tiles"


def _png(color, mode="RGBA", size=(256, 256)) -> bytes:
    buf = io.BytesIO()
    Image.new(mode, size, color).save(buf, "PNG")
    return buf.getvalue()


def _half_transparent_png() -> bytes:
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for x in range(128):
        for y in range(256):
            img.putpixel((x, y), (200, 30, 30, 255))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


class TestRealTiles:
    def test_real_tile_is_image(self):
        v = classify_tile((FIXTURES / "usgs_topo_real.jpg").read_bytes(), "image/jpeg")
        assert v.kind == "image"
        assert v.transparent_fraction == 0.0

    @pytest.mark.parametrize("fixture", [
        "esri_not_available.jpg", "osm_blocked.png", "bing_no_imagery.png"])
    def test_known_placeholders(self, fixture):
        v = classify_tile((FIXTURES / fixture).read_bytes(), "image/png")
        assert v.kind == "placeholder"

    def test_wms_exception_is_error_even_with_200(self):
        v = classify_tile((FIXTURES / "wms_exception.txt").read_bytes(), "WMS_XML")
        assert v.kind == "error"


class TestSyntheticTiles:
    def test_solid_opaque_colour_is_blank(self):
        assert classify_tile(_png((0, 0, 0, 255)), "image/png").kind == "blank"

    def test_fully_transparent_is_empty(self):
        assert classify_tile(_png((0, 0, 0, 0)), "image/png").kind == "empty"

    def test_partly_transparent_overlay_is_image(self):
        v = classify_tile(_half_transparent_png(), "image/png")
        assert v.kind == "image"
        assert v.transparent_fraction == pytest.approx(0.5)

    def test_html_body_is_error(self):
        assert classify_tile(b"<html><body>504 Gateway Time-out</body></html>", "text/html").kind == "error"

    def test_undecodable_bytes_are_error(self):
        assert classify_tile(b"\x89PNG\r\n\x1a\nnot really a png", "image/png").kind == "error"

    def test_empty_body_is_error(self):
        assert classify_tile(b"", "image/png").kind == "error"
