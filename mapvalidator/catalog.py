"""Turn map XML files into catalog entries and the Maps markdown page."""

import html
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from mapvalidator.qr import build_import_uri

# Display/filter order for the map style categories on the Maps page.
CATEGORY_ORDER = [
    "Satellite",
    "Topographic",
    "Street",
    "Nautical",
    "Cycling",
    "Overlay",
    "Land use",
]

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


_ADD_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 5v14M5 12h14"/></svg>'
)


def _cat_class(category: str) -> str:
    """CSS modifier for a category, e.g. 'Land use' -> 'land-use'."""
    return slugify(category) or "other"


def _card_html(entry: dict, meta: dict) -> str:
    """Render one map as a card. ``meta`` is {category, text} or {}."""
    name = html.escape(entry["name"])
    category = meta.get("category") or "Other"
    desc = html.escape(meta.get("text") or "")
    # data-search powers the on-page filter (name + description + provider).
    search = html.escape(
        " ".join((entry["name"], meta.get("text") or "", entry["provider"])).lower(),
        quote=True,
    )
    key_badge = (
        '<span class="am-card__key" title="Requires a free API key">key required</span>'
        if entry["needs_key"]
        else ""
    )
    add_href = html.escape(entry["import_uri"], quote=True)
    src_href = html.escape(entry["raw_url"], quote=True)
    return (
        f'<article class="am-card" data-cat="{html.escape(category, quote=True)}" '
        f'data-search="{search}">'
        '<div class="am-card__top">'
        f'<span class="am-badge am-badge--{_cat_class(category)}">'
        f"{html.escape(category)}</span>"
        f'<span class="am-type">{html.escape(entry["source_type"])}</span>'
        "</div>"
        f'<h3 class="am-card__name">{name}</h3>'
        f'<p class="am-card__desc">{desc}</p>'
        '<div class="am-card__actions">'
        f'<a class="am-btn am-btn--add" href="{add_href}">'
        f"{_ADD_ICON}<span>Add to ATAK</span></a>"
        f'<img class="am-card__qr" src="../qr/{entry["slug"]}.png" '
        f'alt="QR code to add {name} to ATAK" loading="lazy" '
        'title="Scan from another device">'
        "</div>"
        '<div class="am-card__foot">'
        f'<a href="{src_href}">View source</a>'
        f"{key_badge}"
        "</div>"
        "</article>"
    )


def render_maps_page(
    entries: list[dict],
    descriptions: dict | None = None,
    package_uri: str | None = None,
    package_qr: str | None = None,
) -> str:
    """Render the Maps page: an install hero, a category filter, and a card grid.

    ``descriptions`` maps slug -> {category, text}. ``package_uri`` and
    ``package_qr`` (when given) render the "install everything" hero for the
    whole-map-pack data package.
    """
    descriptions = descriptions or {}
    ordered = sorted(entries, key=lambda x: (x["provider"].lower(), x["name"].lower()))
    total = len(ordered)

    out = ["# Maps", ""]

    # Install-everything hero.
    if package_uri and package_qr:
        pkg_href = html.escape(package_uri, quote=True)
        pkg_qr = html.escape(package_qr, quote=True)
        out += [
            '<section class="am-hero">',
            '  <div class="am-hero__body">',
            "    <h2>Install every map at once</h2>",
            f"    <p>Tap the button on your ATAK device, or scan the code from "
            f"another device. Imports one data package with all {total} maps "
            f"(ATAK&nbsp;5.1+).</p>",
            f'    <a class="am-btn am-btn--all" href="{pkg_href}">'
            f"{_ADD_ICON}<span>Add all {total} maps to ATAK</span></a>",
            '    <p class="am-hero__note">Kept in ATAK’s Mission Package '
            "Tool, so you can remove them all later by deleting the package.</p>",
            "  </div>",
            f'  <img class="am-hero__qr" src="{pkg_qr}" '
            'alt="QR code to add all maps to ATAK">',
            "</section>",
            "",
        ]

    # How-it-works.
    out += [
        '<div class="am-how">',
        '  <div class="am-how__step"><span>1</span> On your ATAK device, tap '
        "<b>Add to ATAK</b> and confirm the prompt.</div>",
        '  <div class="am-how__step"><span>2</span> From another device, scan '
        "the <b>QR code</b> with ATAK.</div>",
        "</div>",
        "",
    ]

    # Filter bar: search box + category chips (only for categories present).
    present = [
        c
        for c in CATEGORY_ORDER
        if any(
            (descriptions.get(e["slug"]) or {}).get("category") == c for e in ordered
        )
    ]
    chips = ['<button class="am-chip is-active" data-cat="all">All</button>']
    chips += [
        f'<button class="am-chip" data-cat="{html.escape(c, quote=True)}">'
        f"{html.escape(c)}</button>"
        for c in present
    ]
    out += [
        '<div class="am-filter">',
        '  <input class="am-search" type="search" placeholder="Filter maps…" '
        'aria-label="Filter maps by name">',
        '  <div class="am-chips">' + "".join(chips) + "</div>",
        "</div>",
        '<p class="am-empty" hidden>No maps match your filter.</p>',
        "",
    ]

    # Card grid.
    missing = [e for e in ordered if not descriptions.get(e["slug"])]
    cards = [_card_html(e, descriptions.get(e["slug"]) or {}) for e in ordered]
    out += ['<div class="am-grid">', *cards, "</div>"]

    if missing:
        out += [
            "",
            f"<!-- {len(missing)} maps without a description entry: "
            + ", ".join(e["slug"] for e in missing)
            + " -->",
        ]
    return "\n".join(out)
