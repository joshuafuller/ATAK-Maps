"""Turn map XML files into catalog entries and the Maps markdown page."""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from mapvalidator.qr import build_import_uri

RAW_BASE = "https://raw.githubusercontent.com/joshuafuller/ATAK-Maps/master"

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

SOURCE_TYPE_MAP = {
    "customMapSource": "TMS",
    "customWmsMapSource": "WMS",
    "customMultiLayerMapSource": "Multi-Layer",
}


def slugify(text: str) -> str:
    """Lowercase, collapse runs of non-alphanumerics to '-', trim edges."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def iter_map_files(root: Path) -> list[Path]:
    """Return sorted *.xml map files under root, skipping EXCLUDE_DIRS."""
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")
        ]
        for fname in filenames:
            if fname.lower().endswith(".xml") and not fname.startswith("."):
                files.append(Path(dirpath) / fname)
    return sorted(files)


def build_map_entry(filepath: Path, root: Path, raw_base: str = RAW_BASE) -> dict:
    """Extract catalog metadata + import URI for a single map file."""
    root_el = ET.parse(filepath).getroot()
    provider = filepath.parent.name
    name = root_el.findtext("name", "Unknown")
    source_type = SOURCE_TYPE_MAP.get(root_el.tag, root_el.tag)
    rel = filepath.relative_to(root).as_posix()
    raw_url = f"{raw_base}/{rel}"
    urls = " ".join((u.text or "") for u in root_el.iter("url"))
    return {
        "provider": provider,
        "name": name,
        "source_type": source_type,
        "slug": slugify(f"{provider}-{filepath.stem}"),
        "raw_url": raw_url,
        "import_uri": build_import_uri(raw_url),
        "needs_key": "API_KEY_HERE" in urls,
    }


def render_maps_page(entries: list[dict]) -> str:
    """Render the Maps markdown page grouped by provider."""
    lines = [
        "# Maps",
        "",
        "Scan a QR code with another device, or tap **Add to ATAK** on this "
        "device (requires ATAK 5.1+). Confirm the import prompt in ATAK.",
        "",
    ]
    provider = None
    for e in sorted(entries, key=lambda x: (x["provider"].lower(), x["name"].lower())):
        if e["provider"] != provider:
            provider = e["provider"]
            lines += [f"## {provider}", ""]
        lines += [
            f"### {e['name']}",
            "",
            f"![QR for {e['name']}](qr/{e['slug']}.png)",
            "",
            f"[Add to ATAK]({e['import_uri']}) &nbsp;·&nbsp; "
            f"[Download XML]({e['raw_url']})",
            "",
        ]
        if e["needs_key"]:
            lines += [
                "> Requires a free API key — open the source file for setup "
                "instructions.",
                "",
            ]
    return "\n".join(lines)
