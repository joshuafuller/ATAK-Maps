"""README map list: maps grouped by type, written between the catalog markers.

The "Update Map Catalog" workflow runs this when map files change, so the
README never needs a hand-typed list or count.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from mapvalidator.catalog import iter_map_files, map_slug

START_MARKER = "<!-- MAP_CATALOG_START -->"
END_MARKER = "<!-- MAP_CATALOG_END -->"
EXPLORER_URL = "https://joshuafuller.github.io/ATAK-Maps/maps/"
# Display order; descriptions.yml's "Overlay" is shown as "Overlays", last.
ORDER = [
    "Satellite",
    "Topographic",
    "Street",
    "Nautical",
    "Cycling",
    "Land use",
    "Other",
    "Overlay",
]
LABEL = {"Overlay": "Overlays"}


def readme_catalog(root: Path, descriptions: dict) -> str:
    groups: dict[str, list[str]] = {}
    for f in iter_map_files(root):
        name = ET.parse(f).getroot().findtext("name", "Unknown")
        slug = map_slug(f)
        category = (descriptions.get(slug) or {}).get("category", "Other")
        groups.setdefault(category, []).append(name)
    known = [c for c in ORDER if c in groups] + sorted(
        c for c in groups if c not in ORDER
    )
    lines = ["| Type | Maps |", "|------|------|"]
    for c in known:
        lines.append(
            f"| {LABEL.get(c, c)} | {' · '.join(sorted(groups[c], key=str.lower))} |"
        )
    lines.append("")
    lines.append(
        f"Preview every map live, with filters and its current status, in the [map explorer]({EXPLORER_URL})."
    )
    return "\n".join(lines)


def replace_catalog(text: str, catalog: str) -> str:
    start, end = text.index(START_MARKER), text.index(END_MARKER)
    return text[: start + len(START_MARKER)] + "\n\n" + catalog + "\n\n" + text[end:]
