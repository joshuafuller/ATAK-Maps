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
    # The import must target the Pages-hosted copy (served as application/xml),
    # NOT raw githubusercontent (text/plain) — otherwise ATAK appends .txt and
    # silently drops the map. See mapvalidator.catalog.PAGES_BASE.
    assert e["import_url"] == (
        "https://joshuafuller.github.io/ATAK-Maps/sources/"
        "OrdnanceSurvey/os_road_3857.xml"
    )
    from urllib.parse import quote

    assert quote(e["import_url"], safe="") in e["import_uri"]
    assert "raw.githubusercontent" not in e["import_uri"]
    assert e["import_uri"].startswith("tak://com.atakmap.app/import?url=")
    assert e["needs_key"] is True


_OS_ENTRY = {
    "provider": "OrdnanceSurvey",
    "name": "OS - Road 3857",
    "source_type": "TMS",
    "slug": "ordnancesurvey-os-road-3857",
    "raw_url": "https://raw.example/os.xml",
    "import_uri": "tak://com.atakmap.app/import?url=ENC",
    "needs_key": True,
}


def test_render_maps_page_card_html():
    descriptions = {
        "ordnancesurvey-os-road-3857": {
            "category": "Street",
            "text": "OS road map of Great Britain.",
        }
    }
    md = render_maps_page([_OS_ENTRY], descriptions=descriptions)
    assert 'class="am-card"' in md
    assert 'data-cat="Street"' in md
    assert "am-badge--street" in md
    assert "OS road map of Great Britain." in md
    # the Add-to-ATAK button links the import URI
    assert 'href="tak://com.atakmap.app/import?url=ENC"' in md
    assert "Add to ATAK" in md
    assert "qr/ordnancesurvey-os-road-3857.png" in md
    assert 'href="https://raw.example/os.xml"' in md  # view source
    assert "key required" in md  # needs_key badge
    # a Street filter chip is present
    assert '<button class="am-chip" data-cat="Street">Street</button>' in md


def test_iter_map_files_skips_dot_directories(tmp_path):
    _write(tmp_path, "OrdnanceSurvey/os_road_3857.xml", TMS)
    _write(tmp_path, ".venv/lib/site-packages/mkdocs/templates/sitemap.xml", TMS)
    names = [f.name for f in iter_map_files(tmp_path)]
    assert "os_road_3857.xml" in names
    assert "sitemap.xml" not in names


_USGS_ENTRY = {
    "provider": "USGS",
    "name": "USGS Topo",
    "source_type": "TMS",
    "slug": "usgs-topo",
    "raw_url": "https://raw.example/usgs.xml",
    "import_uri": "tak://com.atakmap.app/import?url=ENC",
    "needs_key": False,
}


def test_render_maps_page_no_key_badge_when_not_needed():
    md = render_maps_page(
        [_USGS_ENTRY],
        descriptions={"usgs-topo": {"category": "Topographic", "text": "t"}},
    )
    assert "key required" not in md


def test_render_maps_page_hero_when_package_given():
    md = render_maps_page(
        [_USGS_ENTRY],
        descriptions={},
        package_uri="tak://com.atakmap.app/import?url=PKG",
        package_qr="qr/_all-maps.png",
    )
    assert "am-hero" in md
    assert 'href="tak://com.atakmap.app/import?url=PKG"' in md
    assert "qr/_all-maps.png" in md
    assert "Add all 1 maps to ATAK" in md


def test_render_maps_page_no_hero_without_package():
    md = render_maps_page([_USGS_ENTRY])
    assert "am-hero" not in md


def test_build_manifest_structure():
    from mapvalidator.catalog import PACKAGE_UID, build_manifest

    md = build_manifest(
        ["BLM/blm_land_ownership_sma.xml", "OrdnanceSurvey/os_road_3857.xml"]
    )
    assert '<MissionPackageManifest version="2">' in md
    assert f'<Parameter name="uid" value="{PACKAGE_UID}"/>' in md
    assert '<Parameter name="onReceiveImport" value="true"/>' in md
    assert '<Content ignore="false" zipEntry="BLM/blm_land_ownership_sma.xml"/>' in md
    assert '<Content ignore="false" zipEntry="OrdnanceSurvey/os_road_3857.xml"/>' in md
    # sorted + well-formed
    import xml.etree.ElementTree as ET

    root = ET.fromstring(md)
    assert root.tag == "MissionPackageManifest"
    assert len(root.find("Contents").findall("Content")) == 2


def test_package_import_uri_targets_pages_pack():
    from mapvalidator.catalog import package_import_uri

    uri = package_import_uri()
    assert uri.startswith("tak://com.atakmap.app/import?url=")
    assert "joshuafuller.github.io%2FATAK-Maps%2Fpack%2Fatak-maps-all.zip" in uri
    assert "raw.githubusercontent" not in uri
