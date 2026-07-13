#!/usr/bin/env python3
"""Generate docs/maps.md and docs/qr/*.png from the repo's map sources."""

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The repo root (containing the mapvalidator package) isn't on sys.path when
# this file is invoked directly as `python scripts/gen_pages_catalog.py`
# (Python only puts the script's own directory there), so add it explicitly.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mapvalidator.catalog import (  # noqa: E402
    SOURCES_SUBDIR,
    build_map_entry,
    iter_map_files,
    render_maps_page,
)

DOCS = REPO_ROOT / "docs"
QR_DIR = DOCS / "qr"
SOURCES_DIR = DOCS / SOURCES_SUBDIR


def write_qr(data: str, out_path: Path) -> None:
    """Write a QR PNG encoding ``data`` (lazy import keeps the module importable)."""
    import qrcode

    out_path.parent.mkdir(parents=True, exist_ok=True)
    qrcode.make(data).save(out_path)


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
    (DOCS / "maps.md").write_text(render_maps_page(entries))
    print(
        f"Generated {len(entries)} map entries + QR codes + hosted sources "
        "into docs/."
    )


if __name__ == "__main__":
    main()
