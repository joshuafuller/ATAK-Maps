"""tileUpdate: how often ATAK re-fetches cached tiles.

ATAK (MobacMapSourceFactory) reads it with Integer.parseInt when it is all
digits, as milliseconds; anything else means "never refresh". Values above
Java's int range throw, so the map would not load.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from mapvalidator.catalog import iter_map_files

REPO = Path(__file__).resolve().parent.parent
JAVA_INT_MAX = 2**31 - 1  # about 24.8 days in milliseconds
WEEK_MS = 7 * 24 * 3600 * 1000


def _tile_update(f: Path) -> str:
    return (ET.parse(f).getroot().findtext("tileUpdate") or "").strip()


def test_numeric_tile_update_fits_in_a_java_int():
    for f in iter_map_files(REPO):
        v = _tile_update(f)
        if v.isdigit():
            assert (
                int(v) <= JAVA_INT_MAX
            ), f"{f.name}: tileUpdate {v} ms overflows ATAK's int parser"


def test_faa_charts_refresh_at_least_weekly():
    # FAA charts change every 28/56 days; without a refresh ATAK keeps old charts forever.
    faa = sorted((REPO / "maps" / "base" / "faa").glob("*.xml"))
    assert faa, "no FAA maps found"
    for f in faa:
        v = _tile_update(f)
        assert v.isdigit() and 0 < int(v) <= WEEK_MS, f"{f.name}: tileUpdate is {v!r}"
