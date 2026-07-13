from pathlib import Path

from mapvalidator.catalog import (
    build_map_entry,
    iter_map_files,
    render_maps_page,
    slugify,
)

TMS = """<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>OS - Road 3857</name>
    <minZoom>0</minZoom>
    <maxZoom>16</maxZoom>
    <tileType>png</tileType>
    <url>https://api.os.uk/x/{$z}/{$x}/{$y}.png?key=API_KEY_HERE</url>
</customMapSource>
"""


def _write(tmp_path, rel, body):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    return p


def test_slugify_basic():
    assert slugify("BLM - Land Ownership (SMA)") == "blm-land-ownership-sma"


def test_slugify_collapses_and_trims():
    assert slugify("  OS __ Road!! ") == "os-road"


def test_iter_map_files_skips_excluded_dirs(tmp_path):
    _write(tmp_path, "OrdnanceSurvey/os_road_3857.xml", TMS)
    _write(tmp_path, "docs/skip.xml", TMS)
    names = [f.name for f in iter_map_files(tmp_path)]
    assert "os_road_3857.xml" in names
    assert "skip.xml" not in names


def test_build_map_entry_fields(tmp_path):
    f = _write(tmp_path, "OrdnanceSurvey/os_road_3857.xml", TMS)
    e = build_map_entry(f, tmp_path, raw_base="https://raw.example/repo/master")
    assert e["provider"] == "OrdnanceSurvey"
    assert e["name"] == "OS - Road 3857"
    assert e["source_type"] == "TMS"
    assert e["slug"] == "ordnancesurvey-os-road-3857"
    assert e["raw_url"] == (
        "https://raw.example/repo/master/OrdnanceSurvey/os_road_3857.xml"
    )
    assert e["import_uri"].startswith("tak://com.atakmap.app/import?url=")
    assert e["needs_key"] is True


def test_render_maps_page_structure():
    entries = [
        {
            "provider": "OrdnanceSurvey",
            "name": "OS - Road 3857",
            "source_type": "TMS",
            "slug": "ordnancesurvey-os-road-3857",
            "raw_url": "https://raw.example/os.xml",
            "import_uri": "tak://com.atakmap.app/import?url=ENC",
            "needs_key": True,
        }
    ]
    md = render_maps_page(entries)
    assert "## OrdnanceSurvey" in md
    assert "![QR for OS - Road 3857](qr/ordnancesurvey-os-road-3857.png)" in md
    assert "[Add to ATAK](tak://com.atakmap.app/import?url=ENC)" in md
    assert "[Download XML](https://raw.example/os.xml)" in md
    assert "Requires a free API key" in md
