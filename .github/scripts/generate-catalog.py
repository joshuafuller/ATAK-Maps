#!/usr/bin/env python3
"""Generate map catalog table for README.md from XML map files."""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = REPO_ROOT / "README.md"
EXCLUDE_DIRS = {
    ".github",
    ".git",
    "schema",
    "dist",
    "docs",
    "mapvalidator",
    "tests",
    "images",
}

START_MARKER = "<!-- MAP_CATALOG_START -->"
END_MARKER = "<!-- MAP_CATALOG_END -->"

SOURCE_TYPE_MAP = {
    "customMapSource": "TMS",
    "customWmsMapSource": "WMS",
    "customMultiLayerMapSource": "Multi-Layer",
}


def find_xml_files():
    """Find all XML files in the repo, excluding certain directories."""
    xml_files = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        # Prune excluded directories so os.walk doesn't descend into them
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        rel = Path(dirpath).relative_to(REPO_ROOT)
        if rel.parts and rel.parts[0] in EXCLUDE_DIRS:
            continue
        for fname in filenames:
            if fname.lower().endswith(".xml"):
                xml_files.append(Path(dirpath) / fname)
    return xml_files


def parse_map_file(filepath):
    """Parse a single XML map file and return its metadata."""
    try:
        tree = ET.parse(filepath)
    except ET.ParseError as e:
        print(f"WARNING: Failed to parse {filepath}: {e}", file=sys.stderr)
        return None

    root = tree.getroot()
    tag = root.tag
    source_type = SOURCE_TYPE_MAP.get(tag)
    if source_type is None:
        print(f"WARNING: Unknown root element <{tag}> in {filepath}", file=sys.stderr)
        source_type = tag

    provider = filepath.parent.name
    name = root.findtext("name", "Unknown")
    min_zoom = root.findtext("minZoom", "—")
    max_zoom = root.findtext("maxZoom", "—")
    tile_type = root.findtext("tileType", "—")

    return {
        "provider": provider,
        "name": name,
        "minZoom": min_zoom,
        "maxZoom": max_zoom,
        "tileType": tile_type,
        "sourceType": source_type,
    }


def generate_table(maps):
    """Generate a markdown table from parsed map data."""
    lines = []
    lines.append("| Provider | Map Name | Zoom (min–max) | Tile Type | Source |")
    lines.append("|----------|----------|----------------|-----------|--------|")
    for m in maps:
        zoom = f"{m['minZoom']}–{m['maxZoom']}"
        lines.append(
            f"| {m['provider']} | {m['name']} | {zoom} | {m['tileType']} | {m['sourceType']} |"
        )
    return "\n".join(lines)


def update_readme(table):
    """Replace content between catalog markers in README.md."""
    content = README_PATH.read_text()

    start_idx = content.find(START_MARKER)
    end_idx = content.find(END_MARKER)

    if start_idx == -1 or end_idx == -1:
        print("ERROR: Could not find catalog markers in README.md", file=sys.stderr)
        sys.exit(1)

    before = content[: start_idx + len(START_MARKER)]
    after = content[end_idx:]

    new_content = before + "\n\n" + table + "\n\n" + after
    README_PATH.write_text(new_content)


def main():
    xml_files = find_xml_files()
    maps = []
    for f in xml_files:
        result = parse_map_file(f)
        if result:
            maps.append(result)

    # Sort by provider (case-insensitive), then by name
    maps.sort(key=lambda m: (m["provider"].lower(), m["name"].lower()))

    table = generate_table(maps)
    update_readme(table)
    print(f"Catalog updated: {len(maps)} maps processed.")


if __name__ == "__main__":
    main()
