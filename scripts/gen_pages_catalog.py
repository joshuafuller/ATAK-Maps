#!/usr/bin/env python3
"""Generate docs/maps.md and docs/qr/*.png from the repo's map sources."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The repo root (containing the mapvalidator package) isn't on sys.path when
# this file is invoked directly as `python scripts/gen_pages_catalog.py`
# (Python only puts the script's own directory there), so add it explicitly.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mapvalidator.catalog import (  # noqa: E402
    build_map_entry,
    iter_map_files,
    render_maps_page,
)

DOCS = REPO_ROOT / "docs"
QR_DIR = DOCS / "qr"


def write_qr(data: str, out_path: Path) -> None:
    """Write a QR PNG encoding ``data`` (lazy import keeps the module importable)."""
    import qrcode

    out_path.parent.mkdir(parents=True, exist_ok=True)
    qrcode.make(data).save(out_path)


def main() -> None:
    entries = [build_map_entry(f, REPO_ROOT) for f in iter_map_files(REPO_ROOT)]
    for e in entries:
        write_qr(e["import_uri"], QR_DIR / f"{e['slug']}.png")
    (DOCS / "maps.md").write_text(render_maps_page(entries))
    print(f"Generated {len(entries)} map entries + QR codes into docs/.")


if __name__ == "__main__":
    main()
