"""README: the map list is generated, and no page carries a hand-typed map count.

Hand-typed counts ("all 40 maps") go stale the moment a map is added, so the
only place a count may appear is inside the generated catalog block.
"""

import re
from pathlib import Path

from mapvalidator.readme import (
    END_MARKER,
    START_MARKER,
    readme_catalog,
    replace_catalog,
)

REPO = Path(__file__).resolve().parent.parent

TMS = """<?xml version="1.0" encoding="UTF-8"?>
<customMapSource><name>{name}</name><maxZoom>18</maxZoom><url>https://t.example/{{$z}}/{{$x}}/{{$y}}.png</url></customMapSource>
"""


def _map(root: Path, rel: str, name: str) -> None:
    f = root / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(TMS.format(name=name))


class TestReadmeCatalog:
    def test_maps_grouped_by_type_overlays_last(self, tmp_path):
        _map(tmp_path, "maps/base/usgs/usgs_topo.xml", "USGS Topo")
        _map(tmp_path, "maps/base/esri/esri_topo.xml", "Esri Topo")
        _map(tmp_path, "maps/base/google/google_satellite.xml", "Google Satellite")
        _map(tmp_path, "maps/overlays/grg_fema_flood.xml", "+ FEMA Flood")
        desc = {
            "usgs-usgs-topo": {"category": "Topographic"},
            "esri-esri-topo": {"category": "Topographic"},
            "google-google-satellite": {"category": "Satellite"},
            "grg-grg-fema-flood": {"category": "Overlay"},
        }
        rows = [
            r
            for r in readme_catalog(tmp_path, desc).splitlines()
            if r.startswith("| ") and "---" not in r
        ]
        assert rows[0].startswith("| Type")
        assert rows[1] == "| Satellite | Google Satellite |"
        assert rows[2] == "| Topographic | Esri Topo · USGS Topo |"
        assert rows[-1] == "| Overlays | + FEMA Flood |"

    def test_map_without_description_is_listed_as_other(self, tmp_path):
        _map(tmp_path, "x/y.xml", "Mystery Map")
        assert "| Other | Mystery Map |" in readme_catalog(tmp_path, {})

    def test_replace_catalog_only_touches_the_block(self):
        text = f"intro\n{START_MARKER}\nold\n{END_MARKER}\noutro\n"
        out = replace_catalog(text, "NEW")
        assert out == f"intro\n{START_MARKER}\n\nNEW\n\n{END_MARKER}\noutro\n"


COUNT = re.compile(r"\b\d{2,}\s+(?:maps?|map sources|sources)\b", re.IGNORECASE)


def _outside_catalog(text: str) -> str:
    if START_MARKER in text and END_MARKER in text:
        start, end = text.index(START_MARKER), text.index(END_MARKER)
        return text[:start] + text[end:]
    return text


def test_no_hand_typed_map_counts():
    pages = [
        REPO / "README.md",
        *sorted((REPO / "docs").glob("*.md")),
        REPO / "docs" / "maps" / "index.html",
    ]
    found = []
    for page in pages:
        for m in COUNT.finditer(_outside_catalog(page.read_text())):
            found.append(f"{page.relative_to(REPO)}: “{m.group(0)}”")
    assert found == [], (
        "Map counts go stale; let the page or the catalog workflow fill them in:\n"
        + "\n".join(found)
    )
