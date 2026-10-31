"""TAK Aware (open-source iOS TAK client) can read our customMapSource maps.

TAK Aware's MapSourceParser (flighttactics/TAKAware,
TAKAware/Parsers/MapSourceParser.swift) reads only <customMapSource> roots and
drops a map unless it has all of: name, url, minZoom, maxZoom, tileType,
tileUpdate, backgroundColor. It does not expand {$serverpart}, so maps that
use it are out of scope. ATAK ignores a non-numeric <tileUpdate> (e.g. None).
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from mapvalidator.catalog import MAPS_DIR, iter_map_files

REPO = Path(__file__).resolve().parent.parent

TAKAWARE_FIELDS = (
    "name",
    "url",
    "minZoom",
    "maxZoom",
    "tileType",
    "tileUpdate",
    "backgroundColor",
)


def takaware_candidates() -> list[Path]:
    out = []
    for f in iter_map_files(REPO / MAPS_DIR):
        root = ET.parse(f).getroot()
        if root.tag != "customMapSource":
            continue
        if "{$serverpart}" in (root.findtext("url") or ""):
            continue
        out.append(f)
    return out


def missing_fields(f: Path) -> list[str]:
    root = ET.parse(f).getroot()
    return [t for t in TAKAWARE_FIELDS if not (root.findtext(t) or "").strip()]


def test_there_are_maps_to_check():
    assert len(takaware_candidates()) > 20


def test_every_custommapsource_has_the_fields_takaware_needs():
    bad = {
        str(f.relative_to(REPO)): missing_fields(f)
        for f in takaware_candidates()
        if missing_fields(f)
    }
    assert bad == {}
