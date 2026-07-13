# ATAK-Maps GitHub Pages Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a MkDocs Material site for ATAK-Maps with a per-map QR code and tappable "Add to ATAK" button, generated from the XML sources and deployed to GitHub Pages, plus a bundle QR + stable release asset for the README.

**Architecture:** A pure `build_import_uri()` produces the `tak://com.atakmap.app/import?url=…` URI. A catalog module turns each map XML into a metadata entry (name, provider, slug, raw URL, import URI) and renders the Maps markdown page. A thin script writes the per-map QR PNGs and `docs/maps.md`. MkDocs Material builds the site (reusing existing `docs/*.md`); a GitHub Actions workflow generates the catalog and deploys to Pages.

**Tech Stack:** Python 3.10+ (stdlib `urllib`, `xml.etree`), `qrcode[pil]` (QR PNGs), `mkdocs-material` (site), GitHub Actions Pages deploy, `uv` for env/runs, `@semantic-release/github` (release asset).

## Global Constraints

- Target ATAK **5.1+** (the version that added the `tak://` URL scheme). State this on the site/README.
- Import URI format is exactly `tak://com.atakmap.app/import?url=<fully percent-encoded URL>` — the `url` value must be percent-encoded including `:` and `/`.
- Per-map import target base: `https://raw.githubusercontent.com/joshuafuller/ATAK-Maps/master`.
- Bundle target (stable): `https://github.com/joshuafuller/ATAK-Maps/releases/latest/download/atak-maps.zip`.
- `docs/qr/` and `docs/maps.md` are **generated + git-ignored**. The bundle QR `images/add-to-atak.png` is **committed** (README renders outside the MkDocs build).
- Do **not** modify any map XML, the schema, or `mapvalidator`'s validate/probe behaviour.
- Python style: `black` line-length 88, `isort` profile black. Tests are pytest; coverage gate `fail_under = 80` over `mapvalidator`.
- Conventional Commits (`feat:`/`fix:`/`docs:`/`ci:`/`chore:`), one logical change per commit.
- New build deps go in a pinned-by-convention `docs` optional-dependencies group; they are build-time only.
- Reuse, don't duplicate: the existing `.github/scripts/generate-catalog.py` (README table) stays untouched.

## File Structure

- Create `mapvalidator/qr.py` — pure import-URI builder. Responsibility: URI format only.
- Create `mapvalidator/catalog.py` — map metadata extraction + Maps-page rendering. Responsibility: turn XML files into catalog entries and markdown; no I/O beyond reading XML.
- Create `scripts/gen_pages_catalog.py` — thin CLI: writes `docs/qr/*.png` + `docs/maps.md`. Responsibility: side effects (QR PNGs, file write).
- Create `tests/test_qr.py`, `tests/test_catalog.py` — unit tests.
- Create `mkdocs.yml` — site config.
- Create `docs/index.md` — landing page.
- Create `.github/workflows/pages.yml` — build + deploy.
- Modify `pyproject.toml` — add `docs` optional-dependencies.
- Modify `.gitignore` — ignore generated site artefacts.
- Modify `.releaserc.json` — constant-named `atak-maps.zip` asset.
- Modify `README.md` — "Add to ATAK" section (committed bundle QR + copy-paste URI + site link).
- Create `images/add-to-atak.png` — committed bundle QR (generated once).
- Create `docs/images/atak-maps-logo.png` — copy of `images/ATAK_MAPS_Logo.png` for the theme logo (MkDocs logo paths are relative to `docs_dir`).

---

### Task 1: Import-URI builder (`mapvalidator/qr.py`)

**Files:**
- Create: `mapvalidator/qr.py`
- Test: `tests/test_qr.py`

**Interfaces:**
- Produces: `build_import_uri(download_url: str) -> str` — returns `"tak://com.atakmap.app/import?url=" + percent_encoded(download_url)`. Also exports `IMPORT_ENDPOINT = "tak://com.atakmap.app/import"`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_qr.py
from mapvalidator.qr import IMPORT_ENDPOINT, build_import_uri


def test_encodes_full_url():
    uri = build_import_uri("https://example.com/a/b.zip?x=1")
    assert uri == (
        "tak://com.atakmap.app/import?url="
        "https%3A%2F%2Fexample.com%2Fa%2Fb.zip%3Fx%3D1"
    )


def test_has_import_endpoint_prefix():
    assert build_import_uri("https://x").startswith(IMPORT_ENDPOINT + "?url=")


def test_slashes_and_colons_are_encoded_not_raw():
    uri = build_import_uri("https://a.com/p")
    # The inner URL's scheme separator must be encoded, not left literal.
    assert "://a.com" not in uri
    assert "url=https%3A%2F%2Fa.com%2Fp" in uri
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_qr.py -o addopts="" -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'mapvalidator.qr'`.

- [ ] **Step 3: Write minimal implementation**

```python
# mapvalidator/qr.py
"""Build ATAK import URIs used by QR codes and 'Add to ATAK' links."""

from urllib.parse import quote

IMPORT_ENDPOINT = "tak://com.atakmap.app/import"


def build_import_uri(download_url: str) -> str:
    """Return the tak:// URI ATAK uses to fetch and import ``download_url``.

    ATAK 5.1+ parses ``tak://com.atakmap.app/import?url=<url-encoded URL>``.
    The url value is fully percent-encoded (``safe=""``) so its own ``:`` and
    ``/`` cannot confuse the outer URI parser.
    """
    return f"{IMPORT_ENDPOINT}?url={quote(download_url, safe='')}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_qr.py -o addopts="" -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Mutation-witness the encoding (repo rigor norm)**

Temporarily change `safe=''` to `safe='/:'` in `build_import_uri`, then run:
`uv run --extra dev pytest tests/test_qr.py -o addopts="" -q`
Expected: FAIL (`test_slashes_and_colons_are_encoded_not_raw` and `test_encodes_full_url` catch it). Then revert the change and re-run: PASS. This proves the tests actually pin the encoding.

- [ ] **Step 6: Commit**

```bash
git add mapvalidator/qr.py tests/test_qr.py
git commit -m "feat: add ATAK import-URI builder for QR/link generation"
```

---

### Task 2: Catalog module (`mapvalidator/catalog.py`)

**Files:**
- Create: `mapvalidator/catalog.py`
- Test: `tests/test_catalog.py`

**Interfaces:**
- Consumes: `mapvalidator.qr.build_import_uri`.
- Produces:
  - `slugify(text: str) -> str`
  - `iter_map_files(root: Path) -> list[Path]` (sorted; skips `EXCLUDE_DIRS`)
  - `build_map_entry(filepath: Path, root: Path, raw_base: str = RAW_BASE) -> dict` with keys `provider, name, source_type, slug, raw_url, import_uri, needs_key`
  - `render_maps_page(entries: list[dict]) -> str`
  - `RAW_BASE = "https://raw.githubusercontent.com/joshuafuller/ATAK-Maps/master"`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_catalog.py
from pathlib import Path

from mapvalidator.catalog import (
    build_map_entry,
    iter_map_files,
    render_maps_page,
    slugify,
)

TMS = """<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>OS - Road 3857</name>
    <minZoom>0</minZoom>
    <maxZoom>16</maxZoom>
    <tileType>png</tileType>
    <url>https://api.os.uk/x/{$z}/{$x}/{$y}.png?key=API_KEY_HERE</url>
</customMapSource>
"""


def _write(tmp_path, rel, body):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    return p


def test_slugify_basic():
    assert slugify("BLM - Land Ownership (SMA)") == "blm-land-ownership-sma"


def test_slugify_collapses_and_trims():
    assert slugify("  OS __ Road!! ") == "os-road"


def test_iter_map_files_skips_excluded_dirs(tmp_path):
    _write(tmp_path, "OrdnanceSurvey/os_road_3857.xml", TMS)
    _write(tmp_path, "docs/skip.xml", TMS)
    names = [f.name for f in iter_map_files(tmp_path)]
    assert "os_road_3857.xml" in names
    assert "skip.xml" not in names


def test_build_map_entry_fields(tmp_path):
    f = _write(tmp_path, "OrdnanceSurvey/os_road_3857.xml", TMS)
    e = build_map_entry(f, tmp_path, raw_base="https://raw.example/repo/master")
    assert e["provider"] == "OrdnanceSurvey"
    assert e["name"] == "OS - Road 3857"
    assert e["source_type"] == "TMS"
    assert e["slug"] == "ordnancesurvey-os-road-3857"
    assert e["raw_url"] == (
        "https://raw.example/repo/master/OrdnanceSurvey/os_road_3857.xml"
    )
    assert e["import_uri"].startswith("tak://com.atakmap.app/import?url=")
    assert e["needs_key"] is True


def test_render_maps_page_structure():
    entries = [
        {
            "provider": "OrdnanceSurvey",
            "name": "OS - Road 3857",
            "source_type": "TMS",
            "slug": "ordnancesurvey-os-road-3857",
            "raw_url": "https://raw.example/os.xml",
            "import_uri": "tak://com.atakmap.app/import?url=ENC",
            "needs_key": True,
        }
    ]
    md = render_maps_page(entries)
    assert "## OrdnanceSurvey" in md
    assert "![QR for OS - Road 3857](qr/ordnancesurvey-os-road-3857.png)" in md
    assert "[Add to ATAK](tak://com.atakmap.app/import?url=ENC)" in md
    assert "[Download XML](https://raw.example/os.xml)" in md
    assert "Requires a free API key" in md
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_catalog.py -o addopts="" -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'mapvalidator.catalog'`.

- [ ] **Step 3: Write minimal implementation**

```python
# mapvalidator/catalog.py
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
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            if fname.lower().endswith(".xml"):
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_catalog.py -o addopts="" -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Run full suite + formatters**

Run: `uv run --extra dev pytest -q` → Expected: all pass, coverage ≥ 80%.
Run: `uv run --with black black --check mapvalidator/ tests/` and `uv run --with isort isort --check-only mapvalidator/ tests/` → Expected: clean (fix with the non-`--check` form if not).

- [ ] **Step 6: Commit**

```bash
git add mapvalidator/catalog.py tests/test_catalog.py
git commit -m "feat: add map catalog extraction and Maps-page rendering"
```

---

### Task 3: Catalog generator script + build deps (`scripts/gen_pages_catalog.py`)

**Files:**
- Create: `scripts/gen_pages_catalog.py`
- Modify: `pyproject.toml` (add `docs` optional-dependencies)
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `mapvalidator.catalog.iter_map_files`, `build_map_entry`, `render_maps_page`.
- Produces: on run, writes `docs/qr/<slug>.png` for every map and `docs/maps.md`.

- [ ] **Step 1: Add the `docs` dependency group to `pyproject.toml`**

Add under `[project.optional-dependencies]` (alongside the existing `dev`):

```toml
docs = ["mkdocs-material", "qrcode[pil]"]
```

- [ ] **Step 2: Add generated artefacts to `.gitignore`**

Append:

```gitignore
# Generated Pages site artefacts
/site/
/docs/qr/
/docs/maps.md
.cache/
```

- [ ] **Step 3: Write the generator script**

```python
# scripts/gen_pages_catalog.py
#!/usr/bin/env python3
"""Generate docs/maps.md and docs/qr/*.png from the repo's map sources."""

from pathlib import Path

from mapvalidator.catalog import (
    build_map_entry,
    iter_map_files,
    render_maps_page,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
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
```

- [ ] **Step 4: Run the generator and verify outputs**

Run: `uv run --extra docs python scripts/gen_pages_catalog.py`
Expected: prints "Generated N map entries…"; `docs/maps.md` exists and `docs/qr/` contains one PNG per map.
Verify: `ls docs/qr/ | wc -l` equals the map count, and `grep -c "Add to ATAK" docs/maps.md` equals the map count.

- [ ] **Step 5: Confirm generated files are git-ignored**

Run: `git status --porcelain docs/maps.md docs/qr/`
Expected: no output (ignored). Only `pyproject.toml`, `.gitignore`, and the script are staged.

- [ ] **Step 6: Commit**

```bash
git add scripts/gen_pages_catalog.py pyproject.toml .gitignore
git commit -m "feat: add Pages catalog generator (QR + maps.md) and docs deps"
```

---

### Task 4: MkDocs site (`mkdocs.yml`, landing page, logo)

**Files:**
- Create: `mkdocs.yml`
- Create: `docs/index.md`
- Create: `docs/images/atak-maps-logo.png` (copy of `images/ATAK_MAPS_Logo.png`)

**Interfaces:**
- Consumes: generated `docs/maps.md` (Task 3), existing `docs/*.md`.
- Produces: a `mkdocs build --strict` that succeeds into `site/`.

- [ ] **Step 1: Copy the logo into the docs tree**

Run: `cp images/ATAK_MAPS_Logo.png docs/images/atak-maps-logo.png`
(MkDocs logo/favicon paths are resolved relative to `docs_dir`.)

- [ ] **Step 2: Write `docs/index.md`**

```markdown
# ATAK-Maps

A curated collection of map sources for [ATAK](https://tak.gov) — scan a QR
code or tap **Add to ATAK** to install a map in seconds (ATAK 5.1+).

- **[Browse the maps](maps.md)** — every source with a QR code and one-tap install.
- **[Installation guide](install-guide.md)** — manual install and troubleshooting.
- **[Create your own](creating-custom-maps.md)** — the MOBAC XML format.

## Install the whole set

Scan this with another device, or [download the bundle](https://github.com/joshuafuller/ATAK-Maps/releases/latest/download/atak-maps.zip):

![Add all maps to ATAK](images/add-to-atak.png)
```

- [ ] **Step 3: Write `mkdocs.yml`**

```yaml
site_name: ATAK-Maps
site_description: Map sources for ATAK — install by QR code or one tap.
site_url: https://joshuafuller.github.io/ATAK-Maps/
repo_url: https://github.com/joshuafuller/ATAK-Maps
docs_dir: docs

theme:
  name: material
  logo: images/atak-maps-logo.png
  favicon: images/atak-maps-logo.png
  palette:
    - scheme: default
      primary: blue grey
      toggle:
        icon: material/weather-night
        name: Switch to dark mode
    - scheme: slate
      primary: blue grey
      toggle:
        icon: material/weather-sunny
        name: Switch to light mode
  features:
    - navigation.instant
    - navigation.top
    - search.suggest
    - content.code.copy

nav:
  - Home: index.md
  - Maps: maps.md
  - Installation: install-guide.md
  - Creating Custom Maps: creating-custom-maps.md
  - XML Reference: xml-reference.md
  - Releases: release-guide.md

exclude_docs: |
  superpowers/

plugins:
  - search
```

- [ ] **Step 4: Copy the committed bundle QR into place for the build**

The build references `docs/images/add-to-atak.png`. Until Task 5 generates the
committed `images/add-to-atak.png`, create a placeholder so `--strict` passes:
Run: `cp images/ATAK_MAPS_Logo.png docs/images/add-to-atak.png`
(Task 5 replaces this with the real bundle QR and wires the committed copy.)

- [ ] **Step 5: Build the site strictly**

Run: `uv run --extra docs python scripts/gen_pages_catalog.py && uv run --extra docs mkdocs build --strict`
Expected: "Documentation built in …/site"; no warnings (strict fails on broken links/nav or missing referenced files).

- [ ] **Step 6: Commit**

```bash
git add mkdocs.yml docs/index.md docs/images/atak-maps-logo.png
git commit -m "feat: add MkDocs Material site config and landing page"
```

---

### Task 5: Bundle install — stable release asset, bundle QR, README section

**Files:**
- Modify: `.releaserc.json` (asset name → constant `atak-maps.zip`)
- Create: `images/add-to-atak.png` (committed bundle QR)
- Modify: `docs/images/add-to-atak.png` (replace Task 4 placeholder with the real QR)
- Modify: `README.md` (add "Add to ATAK" section)

**Interfaces:**
- Consumes: `mapvalidator.qr.build_import_uri`.
- Produces: stable bundle URL `…/releases/latest/download/atak-maps.zip`; committed QR image; README section.

- [ ] **Step 1: Make the release asset constant-named**

In `.releaserc.json`, inside the `@semantic-release/github` `assets[0]`, change:

```json
"name": "atak-maps-${nextRelease.version}.zip",
"label": "atak-maps-${nextRelease.version}.zip"
```

to:

```json
"name": "atak-maps.zip",
"label": "atak-maps.zip"
```

(Leave `"path": "dist/atak-maps.zip"` unchanged — the build already produces it.)

- [ ] **Step 2: Generate the committed bundle QR**

Run:

```bash
uv run --extra docs python -c "
import qrcode
from mapvalidator.qr import build_import_uri
url = 'https://github.com/joshuafuller/ATAK-Maps/releases/latest/download/atak-maps.zip'
qrcode.make(build_import_uri(url)).save('images/add-to-atak.png')
"
cp images/add-to-atak.png docs/images/add-to-atak.png
```

Expected: `images/add-to-atak.png` and `docs/images/add-to-atak.png` are the real bundle QR (not the logo placeholder).

- [ ] **Step 3: Add the "Add to ATAK" section to `README.md`**

Insert immediately after the `## Installation Guide` heading block (before `## Map Catalog`):

```markdown
## Add to ATAK (QR)

**Scan to install the whole map set.** On an ATAK 5.1+ device, scan this QR
(from another screen) — ATAK will download and import every map:

![Add all maps to ATAK](images/add-to-atak.png)

Viewing this on the ATAK device itself? Paste this into the device browser:

`tak://com.atakmap.app/import?url=https%3A%2F%2Fgithub.com%2Fjoshuafuller%2FATAK-Maps%2Freleases%2Flatest%2Fdownload%2Fatak-maps.zip`

> GitHub can't make a `tak://` link tappable in this README. For per-map QR
> codes and one-tap **Add to ATAK** buttons, visit the
> **[ATAK-Maps site](https://joshuafuller.github.io/ATAK-Maps/maps/)**.
```

- [ ] **Step 4: Verify the URI in the README matches the builder output**

Run:

```bash
uv run python -c "
from mapvalidator.qr import build_import_uri
print(build_import_uri('https://github.com/joshuafuller/ATAK-Maps/releases/latest/download/atak-maps.zip'))
"
```

Expected: prints exactly the `tak://…` string pasted in Step 3. If they differ, fix the README to match the generated value.

- [ ] **Step 5: Commit**

```bash
git add .releaserc.json images/add-to-atak.png docs/images/add-to-atak.png README.md
git commit -m "feat: add bundle QR to README and stable atak-maps.zip release asset"
```

---

### Task 6: Pages deploy workflow

**Files:**
- Create: `.github/workflows/pages.yml`

**Interfaces:**
- Consumes: `scripts/gen_pages_catalog.py`, `mkdocs.yml`, the `docs` extra.
- Produces: a Pages deployment on push to `master`.

- [ ] **Step 1: Write the workflow**

```yaml
# .github/workflows/pages.yml
name: Deploy Pages

on:
  push:
    branches: [master]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - name: Generate catalog + QR codes
        run: uv run --extra docs python scripts/gen_pages_catalog.py
      - name: Build site (strict)
        run: uv run --extra docs mkdocs build --strict
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Lint the workflow YAML locally**

Run: `uv run --with pyyaml python -c "import yaml; yaml.safe_load(open('.github/workflows/pages.yml'))"`
Expected: no output (valid YAML).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/pages.yml
git commit -m "ci: deploy MkDocs site to GitHub Pages on push to master"
```

- [ ] **Step 4: Enable GitHub Pages (Actions source) — one-time**

Run:

```bash
gh api -X POST repos/joshuafuller/ATAK-Maps/pages -f build_type=workflow 2>/dev/null \
  || gh api -X PUT repos/joshuafuller/ATAK-Maps/pages -f build_type=workflow
```

Expected: Pages configured with `build_type: workflow`. (If it already exists, the PUT updates it.) If the API path is unavailable, set **Settings → Pages → Source: GitHub Actions** in the repo UI.

---

### Task 7: Integration gate — open PR, merge, release, on-device validation

**Files:** none (process).

- [ ] **Step 1: Push the branch and open the PR**

```bash
git push -u origin feat/pages-site
gh pr create --repo joshuafuller/ATAK-Maps --base master --head feat/pages-site \
  --title "feat: GitHub Pages site with per-map QR and Add-to-ATAK" \
  --body "Implements docs/superpowers/specs/2026-07-13-github-pages-site-design.md. MkDocs Material site generated from the XML sources: per-map QR + tappable Add-to-ATAK, existing docs, Pages deploy. Bundle QR + stable atak-maps.zip asset for the README."
```

- [ ] **Step 2: Confirm CI is green, then merge**

Run: `gh pr checks <PR#> --repo joshuafuller/ATAK-Maps` — wait for green (schema validate, tests, and the Pages build).
Then: `gh pr merge <PR#> --repo joshuafuller/ATAK-Maps --squash --delete-branch`.
Verify the Pages deploy ran on master and the site is live at `https://joshuafuller.github.io/ATAK-Maps/`.

- [ ] **Step 3: Cut a release tag so `atak-maps.zip` exists**

The recently merged BLM / BC-Wildfire / Ordnance Survey maps warrant a release. Ensure a `feat:`/`fix:` commit is on master (this PR's squash is `feat:`), which triggers `map-release.yml` → semantic-release publishes `atak-maps.zip`. Confirm:
Run: `gh release view --repo joshuafuller/ATAK-Maps --json assets --jq '.assets[].name'`
Expected: includes `atak-maps.zip`.
Then confirm the stable URL resolves:
Run: `curl -sIL -o /dev/null -w '%{http_code}\n' https://github.com/joshuafuller/ATAK-Maps/releases/latest/download/atak-maps.zip`
Expected: `200`.

- [ ] **Step 4: On-device validation (resolves the raw-XML question)**

On an ATAK 5.1+ device:
1. Scan the **bundle** QR (README/landing) → confirm the import prompt installs the maps from `atak-maps.zip`.
2. Open the site's Maps page and tap **Add to ATAK** for one map (e.g. `BLM - Land Ownership (SMA)`) → confirm ATAK imports the raw `.xml`.

Record the result in the PR / issue #81. **If raw `.xml` is rejected:** escalate per the spec's contingency — extend `gen_pages_catalog.py` to emit per-map data-package `.zip`s (with `MANIFEST/manifest.xml`) into the site output and point `build_map_entry`'s `import_uri` at those hosted zips instead of the raw URL. (That escalation is a follow-up task, only if validation fails.)

---

## Notes for the implementer

- Run everything through `uv`. Tests: `uv run --extra dev pytest -q`. Site: `uv run --extra docs …`.
- The generated `docs/maps.md` and `docs/qr/` are git-ignored on purpose — never commit them; CI regenerates them each deploy.
- Keep `mapvalidator/qr.py` dependency-free (stdlib only) so the test suite needs no new deps; `qrcode` is imported lazily only inside the script's `write_qr`.
- Do not touch map XML, `schema/`, or `mapvalidator`'s validate/probe modules.
