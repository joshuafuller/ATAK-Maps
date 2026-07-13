"""Turn map XML files into catalog entries and the Maps markdown page."""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from mapvalidator.qr import build_import_uri

RAW_BASE = "https://raw.githubusercontent.com/joshuafuller/ATAK-Maps/master"

# The tak:// import target must be served with an XML content type. raw
# githubusercontent serves .xml as text/plain, which makes ATAK's
# ImportFileDownloader append a ".txt" extension (Content-Type -> extension),
# so no map-source resolver claims the file and the import silently no-ops.
# GitHub Pages serves .xml as application/xml, so the site hosts a copy of
# every source under /sources/<path> and the import points there instead.
PAGES_BASE = "https://joshuafuller.github.io/ATAK-Maps"
# Directory (relative to the MkDocs docs dir) the generator copies sources into.
SOURCES_SUBDIR = "sources"

# Whole-map-pack: an ATAK data package (Mission Package) bundling every source,
# served from the site. One QR/link installs the full set. UID is fixed so
# re-imports are recognised as the same package.
PACKAGE_SUBDIR = "pack"
PACKAGE_FILENAME = "atak-maps-all.zip"
PACKAGE_UID = "4e29c057-7d12-40cb-9651-01b9bec4edf3"
PACKAGE_NAME = "ATAK-Maps - All Maps"


def build_manifest(zip_entries: list[str]) -> str:
    """Return the MANIFEST/manifest.xml (Mission Package v2) for the data package.

    ``zip_entries`` are the in-zip paths of the bundled source XML files. Format
    matches ATAK's MissionPackageManifest: a Configuration block (uid/name and
    onReceiveImport=true so ATAK imports the contents) and a Contents block with
    one <Content zipEntry="..."/> per file.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<MissionPackageManifest version="2">',
        "   <Configuration>",
        f'      <Parameter name="uid" value="{PACKAGE_UID}"/>',
        f'      <Parameter name="name" value="{PACKAGE_NAME}"/>',
        '      <Parameter name="onReceiveImport" value="true"/>',
        '      <Parameter name="onReceiveDelete" value="false"/>',
        "   </Configuration>",
        "   <Contents>",
    ]
    for entry in sorted(zip_entries):
        lines.append(f'      <Content ignore="false" zipEntry="{entry}"/>')
    lines += ["   </Contents>", "</MissionPackageManifest>", ""]
    return "\n".join(lines)


def package_import_uri() -> str:
    """tak:// import URI for the whole-map-pack data package hosted on Pages."""
    return build_import_uri(f"{PAGES_BASE}/{PACKAGE_SUBDIR}/{PACKAGE_FILENAME}")


EXCLUDE_DIRS = {
    ".github",
    ".git",
    "schema",
    "dist",
    "site",
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
    # The import must fetch the XML with an application/xml content type; the
    # Pages-hosted copy provides that (see PAGES_BASE note above). raw_url is
    # kept only for the human-facing "view source" link.
    import_url = f"{PAGES_BASE}/{SOURCES_SUBDIR}/{rel}"
    urls = " ".join((u.text or "") for u in root_el.iter("url"))
    return {
        "provider": provider,
        "name": name,
        "source_type": source_type,
        "slug": slugify(f"{provider}-{filepath.stem}"),
        "raw_url": raw_url,
        "import_url": import_url,
        "import_uri": build_import_uri(import_url),
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
