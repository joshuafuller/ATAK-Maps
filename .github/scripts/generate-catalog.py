#!/usr/bin/env python3
"""Write the README map list (maps grouped by type) between the catalog markers.

Run by the "Update Map Catalog" workflow when map files change. The logic is
in mapvalidator.readme (tested in tests/test_readme.py).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402

from mapvalidator.readme import readme_catalog, replace_catalog  # noqa: E402


def main() -> None:
    descriptions = yaml.safe_load((REPO_ROOT / "descriptions.yml").read_text()) or {}
    readme = REPO_ROOT / "README.md"
    readme.write_text(
        replace_catalog(readme.read_text(), readme_catalog(REPO_ROOT, descriptions))
    )
    print("README map list updated.")


if __name__ == "__main__":
    main()
