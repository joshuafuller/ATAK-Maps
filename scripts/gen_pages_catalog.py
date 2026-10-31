#!/usr/bin/env python3
"""Generate the site's map data from the repo's map sources.

Writes the map explorer data (docs/maps/maps.js, docs/maps/health.js), QR
codes (docs/qr/), hosted copies of each source (docs/sources/) and the
all-maps data package (docs/pack/).
"""

import json
import os

import shutil
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The repo root (containing the mapvalidator package) isn't on sys.path when
# this file is invoked directly as `python scripts/gen_pages_catalog.py`
# (Python only puts the script's own directory there), so add it explicitly.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mapvalidator.catalog import (  # noqa: E402
    PACKAGE_FILENAME,
    PACKAGE_SUBDIR,
    SOURCES_SUBDIR,
    build_manifest,
    build_map_entry,
    iter_map_files,
    package_import_uri,
)
from mapvalidator.explorer import (  # noqa: E402
    LIVE_POINTS,
    build_explorer_data,
    health_js,
)  # noqa: E402

DOCS = REPO_ROOT / "docs"
QR_DIR = DOCS / "qr"
SOURCES_DIR = DOCS / SOURCES_SUBDIR
PACKAGE_DIR = DOCS / PACKAGE_SUBDIR
DESCRIPTIONS_FILE = REPO_ROOT / "descriptions.yml"
EXPLORER_DIR = DOCS / "maps"
# map-health.json from the weekly ATAK harness run (the Pages workflow downloads
# it); missing means the explorer shows no health status.
HEALTH_FILE = Path(os.environ.get("MAP_HEALTH_JSON", REPO_ROOT / "map-health.json"))


def write_qr(data: str, out_path: Path) -> None:
    """Write a QR PNG encoding ``data`` (lazy import keeps the module importable)."""
    import qrcode

    out_path.parent.mkdir(parents=True, exist_ok=True)
    qrcode.make(data).save(out_path)


def load_descriptions() -> dict:
    """Load descriptions.yml (slug -> {category, text}); {} if absent."""
    if not DESCRIPTIONS_FILE.exists():
        return {}
    import yaml

    return yaml.safe_load(DESCRIPTIONS_FILE.read_text()) or {}


def build_data_package(map_files: list[Path], out_zip: Path) -> None:
    """Write an ATAK data package (Mission Package .zip) bundling every source.

    Contains MANIFEST/manifest.xml plus each source XML at its provider/name
    path (the manifest's zipEntry). Served from the site so one QR installs the
    whole set.
    """
    zip_entries = [f.relative_to(REPO_ROOT).as_posix() for f in map_files]
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("MANIFEST/manifest.xml", build_manifest(zip_entries))
        for f, entry in zip(map_files, zip_entries):
            z.write(f, entry)


def main() -> None:
    map_files = iter_map_files(REPO_ROOT)
    entries = [build_map_entry(f, REPO_ROOT) for f in map_files]
    for e in entries:
        write_qr(e["import_uri"], QR_DIR / f"{e['slug']}.png")
    # Publish a copy of each source XML on the site so ATAK fetches it with an
    # application/xml content type (raw githubusercontent serves text/plain,
    # which breaks ATAK's import — see mapvalidator.catalog.PAGES_BASE).
    for f in map_files:
        dest = SOURCES_DIR / f.relative_to(REPO_ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f, dest)
    build_data_package(map_files, PACKAGE_DIR / PACKAGE_FILENAME)
    # QR for the whole-map-pack, shown in the Maps-page hero.
    write_qr(package_import_uri(), QR_DIR / "_all-maps.png")
    descriptions = load_descriptions()
    missing = [e["slug"] for e in entries if not descriptions.get(e["slug"])]
    if missing:
        print(f"WARNING: {len(missing)} maps without a description: {missing}")
    maps = build_explorer_data(REPO_ROOT, descriptions, live_points=LIVE_POINTS)
    EXPLORER_DIR.mkdir(parents=True, exist_ok=True)
    (EXPLORER_DIR / "maps.js").write_text(
        "window.ATAK_MAPS = "
        + json.dumps(maps, indent=1)
        + ";\nwindow.ATAK_PACKAGE_URI = "
        + json.dumps(package_import_uri())
        + ";\n"
    )
    (EXPLORER_DIR / "health.js").write_text(health_js(HEALTH_FILE))
    print(
        f"Generated {len(entries)} map entries + QR codes + hosted sources + "
        "data package into docs/."
    )


if __name__ == "__main__":
    main()
