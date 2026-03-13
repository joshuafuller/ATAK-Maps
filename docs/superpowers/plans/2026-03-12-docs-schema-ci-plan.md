# ATAK-Maps Docs, Schema & CI Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul ATAK-Maps documentation with source-of-truth XML reference, add XSD schema with CI validation, auto-generate map catalog, and create visual diagrams.

**Architecture:** Parallel workstreams — XSD schema, documentation (3 files), CI workflows, and Gemini visuals. Schema must complete before CI validation workflow. All other tracks are independent.

**Tech Stack:** XSD 1.0, GitHub Actions, xmllint, shell scripting, Gemini MCP for image generation

**Spec:** `docs/superpowers/specs/2026-03-12-docs-schema-ci-design.md`

**Branch:** `docs/schema-ci-overhaul` (PR to `master`)

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `schema/mobac-maps.xsd` | XSD schema for all 3 XML types |
| Create | `docs/install-guide.md` | User-focused installation guide |
| Create | `docs/xml-reference.md` | Complete MOBAC XML spec from ATAK source |
| Rewrite | `docs/creating-custom-maps.md` | Quickstart tutorial, links to xml-reference |
| Create | `.github/workflows/validate-maps.yml` | Schema validation CI |
| Create | `.github/scripts/generate-catalog.py` | Script to parse XML and generate catalog table |
| Create | `.github/workflows/generate-catalog.yml` | Auto-catalog CI |
| Modify | `README.md` | Add Map Catalog section + update links |
| Modify | `.github/workflows/super-linter.yml` | Remove VALIDATE_XML (replaced by schema validation) |
| Update | `CLAUDE.md` | Reflect new structure |
| Create | `docs/images/install-flow.png` | Gemini: install flowchart |
| Create | `docs/images/xml-anatomy.png` | Gemini: annotated XML diagram |
| Create | `docs/images/directory-layout.png` | Gemini: ATAK directory tree |

---

## Chunk 1: XSD Schema

### Task 1: Create XSD schema for customMapSource

**Files:**
- Create: `schema/mobac-maps.xsd`

Source of truth: `/home/user/development/tak.gov/atak-civ-client/takkernel/engine/src/main/java/com/atakmap/map/layer/raster/mobac/MobacMapSourceFactory.java`

- [ ] **Step 1: Create schema file with customMapSource type**

Create `schema/mobac-maps.xsd` with the `customMapSourceType` complex type:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">

  <!-- Simple types -->
  <xs:simpleType name="tileTypeEnum">
    <xs:restriction base="xs:string">
      <xs:enumeration value="png"/>
      <xs:enumeration value="jpg"/>
      <xs:enumeration value="PNG"/>
      <xs:enumeration value="JPG"/>
    </xs:restriction>
  </xs:simpleType>

  <xs:simpleType name="hexColor">
    <xs:restriction base="xs:string">
      <xs:pattern value="#[0-9A-Fa-f]{6}"/>
    </xs:restriction>
  </xs:simpleType>

  <xs:simpleType name="epsgCode">
    <xs:restriction base="xs:string">
      <xs:pattern value="EPSG:[0-9]+"/>
    </xs:restriction>
  </xs:simpleType>

  <!-- customMapSource -->
  <xs:complexType name="customMapSourceType">
    <xs:all>
      <xs:element name="name" type="xs:string"/>
      <xs:element name="url" type="xs:string"/>
      <xs:element name="maxZoom" type="xs:nonNegativeInteger"/>
      <xs:element name="minZoom" type="xs:nonNegativeInteger" minOccurs="0"/>
      <xs:element name="tileType" type="tileTypeEnum" minOccurs="0"/>
      <xs:element name="tileUpdate" type="xs:string" minOccurs="0"/>
      <xs:element name="serverParts" type="xs:string" minOccurs="0"/>
      <xs:element name="invertYCoordinate" type="xs:boolean" minOccurs="0"/>
      <xs:element name="backgroundColor" type="hexColor" minOccurs="0"/>
      <xs:element name="coordinatesystem" type="epsgCode" minOccurs="0"/>
      <xs:element name="coordinateSystem" type="epsgCode" minOccurs="0"/>
      <xs:element name="ignoreErrors" type="xs:boolean" minOccurs="0"/>
    </xs:all>
  </xs:complexType>

  <xs:element name="customMapSource" type="customMapSourceType"/>

</xs:schema>
```

- [ ] **Step 2: Validate existing customMapSource XML files against schema**

```bash
cd /home/user/development/ATAK-Maps
for f in Bing/*.xml Google/*.xml ESRI/*.xml opentopo/*.xml usgs/*.xml cycleosm/*.xml michelin/*.xml mtbmapcz/*.xml openseamap/*.xml NAIP/*.xml; do
  echo "--- $f ---"
  xmllint --schema schema/mobac-maps.xsd "$f" --noout 2>&1
done
```

Fix any schema issues revealed by validation (adjust types/patterns as needed to match what actually exists in the repo).

### Task 2: Add customWmsMapSource and customMultiLayerMapSource types

**Files:**
- Modify: `schema/mobac-maps.xsd`

- [ ] **Step 1: Add customWmsMapSource type to schema**

Add after the customMapSource type definition:

```xml
  <!-- customWmsMapSource -->
  <xs:complexType name="customWmsMapSourceType">
    <xs:all>
      <xs:element name="name" type="xs:string"/>
      <xs:element name="url" type="xs:string"/>
      <xs:element name="layers" type="xs:string"/>
      <xs:element name="maxZoom" type="xs:nonNegativeInteger"/>
      <xs:element name="tileType" type="tileTypeEnum"/>
      <xs:element name="minZoom" type="xs:integer" minOccurs="0"/>
      <xs:element name="styles" type="xs:string" minOccurs="0"/>
      <xs:element name="version" type="xs:string" minOccurs="0"/>
      <xs:element name="coordinatesystem" type="epsgCode" minOccurs="0"/>
      <xs:element name="coordinateSystem" type="epsgCode" minOccurs="0"/>
      <xs:element name="aditionalparameters" type="xs:string" minOccurs="0"/>
      <xs:element name="additionalparameters" type="xs:string" minOccurs="0"/>
      <xs:element name="backgroundColor" type="hexColor" minOccurs="0"/>
      <xs:element name="north" type="xs:decimal" minOccurs="0"/>
      <xs:element name="south" type="xs:decimal" minOccurs="0"/>
      <xs:element name="east" type="xs:decimal" minOccurs="0"/>
      <xs:element name="west" type="xs:decimal" minOccurs="0"/>
      <xs:element name="tileUpdate" type="xs:string" minOccurs="0"/>
    </xs:all>
  </xs:complexType>

  <xs:element name="customWmsMapSource" type="customWmsMapSourceType"/>
```

- [ ] **Step 2: Add customMultiLayerMapSource type**

```xml
  <!-- customMultiLayerMapSource -->
  <xs:complexType name="customMultiLayerMapSourceType">
    <xs:all>
      <xs:element name="name" type="xs:string"/>
      <xs:element name="backgroundColor" type="hexColor" minOccurs="0"/>
      <xs:element name="layersAlpha" type="xs:string" minOccurs="0"/>
      <xs:element name="layers">
        <xs:complexType>
          <xs:choice maxOccurs="unbounded">
            <xs:element name="customMapSource" type="customMapSourceType"/>
            <xs:element name="customWmsMapSource" type="customWmsMapSourceType"/>
          </xs:choice>
        </xs:complexType>
      </xs:element>
    </xs:all>
  </xs:complexType>

  <xs:element name="customMultiLayerMapSource" type="customMultiLayerMapSourceType"/>
```

- [ ] **Step 3: Validate ALL XML files in repo against schema**

```bash
cd /home/user/development/ATAK-Maps
FAIL=0
for f in $(find . -name '*.xml' -not -path './.github/*'); do
  xmllint --schema schema/mobac-maps.xsd "$f" --noout 2>&1 || FAIL=1
done
echo "Result: $( [ $FAIL -eq 0 ] && echo PASS || echo FAIL )"
```

All 36 XML files must validate. Fix schema if needed.

- [ ] **Step 4: Commit schema**

```bash
git add schema/mobac-maps.xsd
git commit -m "feat: add XSD schema for MOBAC XML map validation

First formal schema for MOBAC customMapSource, customWmsMapSource,
and customMultiLayerMapSource XML formats. Derived from ATAK's
MobacMapSourceFactory.java parser validation rules."
```

---

## Chunk 2: Documentation

### Task 3: Write xml-reference.md

**Files:**
- Create: `docs/xml-reference.md`

Source of truth files in `/home/user/development/tak.gov/atak-civ-client/takkernel/engine/src/main/java/com/atakmap/map/layer/raster/mobac/`:
- `MobacMapSourceFactory.java` (parser, validation rules)
- `CustomMobacMapSource.java` (URL placeholders, getUrl() method)
- `CustomWmsMobacMapSource.java` (WMS URL construction)
- `CustomMultiLayerMobacMapSource.java` (compositing)

- [ ] **Step 1: Write xml-reference.md**

Complete XML reference document covering:

1. **Overview** — three XML root types, when to use each
2. **`customMapSource` Reference** — element table (name, type, required?, default, description), full example
3. **`customWmsMapSource` Reference** — same format, WMS-specific notes, CDATA usage
4. **`customMultiLayerMapSource` Reference** — composite layers, `layersAlpha`
5. **URL Placeholders** — `{$z}`, `{$x}`, `{$y}`, `{$q}` (with quadkey algorithm explanation), `{$serverpart}`
6. **Server Load Balancing** — `serverParts` examples (space-separated: `a b c`, comma-separated: `t1,t2,t3`, numeric: `1 2 3 4`)
7. **Coordinate Systems** — EPSG:3857 vs 4326, when to use each
8. **Cache Control** — `tileUpdate` as millisecond TTL (0 = never refresh, 604800000 = 1 week)
9. **Known Quirks** — `aditionalparameters` typo, `coordinatesystem` vs `coordinateSystem`, `tileUpdate` string "None" vs integer
10. **Element Quick Reference** — single table with all elements across all types
11. **Validation** — link to XSD schema, how CI validates

Each section should include a real example from the repo where possible.

- [ ] **Step 2: Commit**

```bash
git add docs/xml-reference.md
git commit -m "docs: add complete MOBAC XML reference from ATAK source

Covers all 3 XML types (customMapSource, customWmsMapSource,
customMultiLayerMapSource), URL placeholders, serverParts,
coordinate systems, cache control, and known quirks."
```

### Task 4: Write install-guide.md

**Files:**
- Create: `docs/install-guide.md`

- [ ] **Step 1: Write install-guide.md**

Sections:
1. **Quick Start** — 4 steps: download, extract, copy, verify
2. **Download** — link to Releases page, what the ZIP contains
3. **Install on Android** — step-by-step file manager instructions
   - Base maps → `atak/imagery/mobile/mapsources/` OR `atak/imagery/` (both work)
   - Overlays (files prefixed `grg_`) → `atak/grg/`
   - Alternative path: `atak/mobac/mapsources/`
4. **Verify in ATAK** — how to check maps appear, select a map layer
5. **Installing Individual Maps** — browse the repo, download specific XML files
6. **Offline Caching** — how to cache map tiles for offline use in ATAK
7. **Troubleshooting** — maps not appearing, blank tiles, wrong directory
8. **Map Catalog** — link to catalog in README

Reference diagrams from `docs/images/` (install-flow.png, directory-layout.png).

- [ ] **Step 2: Commit**

```bash
git add docs/install-guide.md
git commit -m "docs: add user-focused install guide

Step-by-step guide for downloading and installing ATAK-Maps,
with troubleshooting and offline caching instructions."
```

### Task 5: Rewrite creating-custom-maps.md

**Files:**
- Modify: `docs/creating-custom-maps.md`

- [ ] **Step 1: Rewrite as quickstart tutorial**

Keep it short and practical:
1. **Intro** — 2-3 sentences, link to xml-reference.md for full spec
2. **Create Your First Map** — walkthrough creating a simple customMapSource XML
3. **Test It** — copy to device, verify in ATAK
4. **Submit It** — PR process, conventional commits
5. **Next Steps** — links to xml-reference.md (WMS, multi-layer, advanced features)

Reference the xml-anatomy.png diagram.

- [ ] **Step 2: Commit**

```bash
git add docs/creating-custom-maps.md
git commit -m "docs: rewrite creating-custom-maps as quickstart tutorial

Simplified to a focused walkthrough with links to the full
XML reference for advanced features."
```

---

## Chunk 3: CI/CD Workflows

### Task 6: Create schema validation workflow

**Files:**
- Create: `.github/workflows/validate-maps.yml`
- Modify: `.github/workflows/super-linter.yml`

- [ ] **Step 1: Create validate-maps.yml**

```yaml
name: Validate Map XML

on:
  pull_request:
    paths:
      - "**/*.xml"
      - "schema/**"
  push:
    branches: [master]
    paths:
      - "**/*.xml"
      - "schema/**"

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install xmllint
        run: sudo apt-get install -y libxml2-utils

      - name: Validate XML files against schema
        run: |
          FAIL=0
          for f in $(find . -name '*.xml' -not -path './.github/*'); do
            echo "Validating: $f"
            if ! xmllint --schema schema/mobac-maps.xsd "$f" --noout 2>&1; then
              FAIL=1
            fi
          done
          exit $FAIL
```

- [ ] **Step 2: Remove VALIDATE_XML from super-linter.yml**

In `.github/workflows/super-linter.yml`, the XML validation is now handled by our schema validator. Either remove the workflow entirely or change `VALIDATE_XML: true` to `VALIDATE_XML: false`. Keeping the workflow for potential future non-XML linting is fine — just disable XML.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/validate-maps.yml .github/workflows/super-linter.yml
git commit -m "ci: add XSD schema validation, replace generic XML linting

New validate-maps.yml validates all XML files against
schema/mobac-maps.xsd. Disables super-linter XML validation
to avoid redundancy."
```

### Task 7: Create auto-catalog generator

**Files:**
- Create: `.github/scripts/generate-catalog.py`
- Create: `.github/workflows/generate-catalog.yml`
- Modify: `README.md`

- [ ] **Step 1: Create generate-catalog.py**

Python script that:
1. Finds all XML files (excluding `.github/`)
2. Parses each with `xml.etree.ElementTree`
3. Extracts: provider (directory name), name, minZoom, maxZoom, tileType, source type (TMS/WMS/Multi based on root element)
4. Sorts by provider then name
5. Generates markdown table
6. Reads README.md, replaces content between `<!-- MAP_CATALOG_START -->` and `<!-- MAP_CATALOG_END -->` markers
7. Writes updated README.md

```python
#!/usr/bin/env python3
"""Generate map catalog table for README.md from XML map files."""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_map_file(filepath):
    """Extract metadata from a MOBAC XML file."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError:
        print(f"WARNING: Could not parse {filepath}", file=sys.stderr)
        return None

    tag = root.tag
    source_type = {
        "customMapSource": "TMS",
        "customWmsMapSource": "WMS",
        "customMultiLayerMapSource": "Multi-Layer",
    }.get(tag, "Unknown")

    name = root.findtext("name", "Unknown")
    min_zoom = root.findtext("minZoom", "0")
    max_zoom = root.findtext("maxZoom", "?")
    tile_type = root.findtext("tileType", "—")
    provider = Path(filepath).parent.name

    return {
        "provider": provider,
        "name": name,
        "zoom": f"{min_zoom}–{max_zoom}",
        "source_type": source_type,
        "tile_type": tile_type,
    }

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    xml_files = sorted(
        f for f in repo_root.rglob("*.xml")
        if ".github" not in f.parts and "schema" not in f.parts
    )

    maps = []
    for f in xml_files:
        meta = parse_map_file(f)
        if meta:
            maps.append(meta)

    maps.sort(key=lambda m: (m["provider"].lower(), m["name"].lower()))

    lines = [
        "| Provider | Map Name | Zoom | Source Type | Tile Format |",
        "|----------|----------|------|-------------|-------------|",
    ]
    for m in maps:
        lines.append(
            f"| {m['provider']} | {m['name']} | {m['zoom']} "
            f"| {m['source_type']} | {m['tile_type']} |"
        )

    catalog = "\n".join(lines)

    readme_path = repo_root / "README.md"
    readme = readme_path.read_text()

    start_marker = "<!-- MAP_CATALOG_START -->"
    end_marker = "<!-- MAP_CATALOG_END -->"

    if start_marker in readme and end_marker in readme:
        before = readme[: readme.index(start_marker) + len(start_marker)]
        after = readme[readme.index(end_marker):]
        readme = f"{before}\n\n{catalog}\n\n{after}"
    else:
        print("WARNING: Catalog markers not found in README.md", file=sys.stderr)
        sys.exit(1)

    readme_path.write_text(readme)
    print(f"Updated catalog with {len(maps)} maps")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add catalog markers to README.md**

Insert after the Installation Guide section in README.md:

```markdown
## Map Catalog

All available map layers, auto-generated from the XML files in this repository:

<!-- MAP_CATALOG_START -->

| Provider | Map Name | Zoom | Source Type | Tile Format |
|----------|----------|------|-------------|-------------|

<!-- MAP_CATALOG_END -->
```

- [ ] **Step 3: Run generate-catalog.py locally to populate the table**

```bash
cd /home/user/development/ATAK-Maps
python3 .github/scripts/generate-catalog.py
```

Verify README.md now has the full catalog table.

- [ ] **Step 4: Create generate-catalog.yml workflow**

```yaml
name: Update Map Catalog

on:
  push:
    branches: [master]
    paths:
      - "**/*.xml"

jobs:
  catalog:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Generate catalog
        run: python3 .github/scripts/generate-catalog.py

      - name: Commit updated catalog
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git diff --quiet README.md || {
            git add README.md
            git commit -m "docs: auto-update map catalog [skip ci]"
            git push
          }
```

- [ ] **Step 5: Commit**

```bash
git add .github/scripts/generate-catalog.py .github/workflows/generate-catalog.yml README.md
git commit -m "ci: add auto-generated map catalog in README

Python script parses all XML files and generates a markdown table
in README.md. GitHub Actions workflow runs on push to master
when XML files change."
```

---

## Chunk 4: Visuals & Final Polish

### Task 8: Generate diagrams with Gemini MCP

**Files:**
- Create: `docs/images/install-flow.png`
- Create: `docs/images/xml-anatomy.png`
- Create: `docs/images/directory-layout.png`

- [ ] **Step 1: Generate install-flow.png**

Use `mcp__gemini-image__gemini_generate_image` to create a clean flowchart showing:
- Step 1: Go to GitHub Releases
- Step 2: Download atak-maps.zip
- Step 3: Extract ZIP
- Step 4: Copy base maps to ATAK/imagery/mobile/mapsources/
- Step 5: Copy overlays (grg_*) to ATAK/grg/
- Step 6: Open ATAK and verify

Style: clean technical diagram, dark background, white text, colored step boxes.

Save to `docs/images/install-flow.png`.

- [ ] **Step 2: Generate xml-anatomy.png**

Use Gemini to create an annotated XML snippet showing a `customMapSource` with callout labels for each element explaining its purpose. Include both required and optional elements.

Save to `docs/images/xml-anatomy.png`.

- [ ] **Step 3: Generate directory-layout.png**

Use Gemini to create a directory tree diagram showing:
```
Android Device
└── atak/
    ├── imagery/
    │   └── mobile/
    │       └── mapsources/    ← Base map XML files go here
    ├── mobac/
    │   └── mapsources/        ← Alternative location
    └── grg/                   ← Overlay XML files (grg_*) go here
```

Save to `docs/images/directory-layout.png`.

- [ ] **Step 4: Add images to docs**

Insert image references into install-guide.md and creating-custom-maps.md where appropriate.

- [ ] **Step 5: Commit**

```bash
git add docs/images/
git commit -m "docs: add Gemini-generated diagrams for install flow, XML anatomy, and directory layout"
```

### Task 9: Update CLAUDE.md and README.md

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

- [ ] **Step 1: Update CLAUDE.md**

Update to reflect:
- New docs structure (install-guide.md, xml-reference.md, creating-custom-maps.md rewrite)
- Schema location (`schema/mobac-maps.xsd`)
- Updated CI pipeline descriptions (validate-maps, generate-catalog)
- Updated PR review checklist

- [ ] **Step 2: Update README.md links**

Update the "Creating Custom Maps" and "Installation Guide" sections to link to the new docs:
- Installation → `docs/install-guide.md`
- Creating Custom Maps → still `docs/creating-custom-maps.md` (now links to xml-reference)
- Add link to `docs/xml-reference.md` for contributors

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs: update CLAUDE.md and README with new doc structure"
```

### Task 10: Open PR

- [ ] **Step 1: Push branch and create PR**

```bash
cd /home/user/development/ATAK-Maps
git push -u origin docs/schema-ci-overhaul
gh pr create \
  --title "docs: overhaul documentation, add XSD schema and CI automation" \
  --body "$(cat <<'EOF'
## Summary
- Add complete MOBAC XML reference derived from ATAK source code (all 3 XML types)
- Add XSD schema for CI validation — first formal MOBAC schema anywhere
- Add user-focused install guide with visual diagrams
- Rewrite creating-custom-maps.md as quickstart tutorial
- Add CI workflow for schema validation on PRs
- Add auto-generated map catalog in README
- Add Gemini-generated diagrams (install flow, XML anatomy, directory layout)

## Test plan
- [ ] All 36 XML files validate against the XSD schema
- [ ] CI workflows pass on the PR
- [ ] Documentation renders correctly on GitHub
- [ ] Map catalog table is accurate and complete
- [ ] Images display properly in markdown
EOF
)"
```

---

## Parallelism Map

```
Task 1-2 (Schema)  ──────────┐
                              ├──→ Task 6 (CI: validate-maps)
Task 3 (xml-reference.md)    │
Task 4 (install-guide.md)    ├──→ Task 9 (CLAUDE.md + README)  ──→ Task 10 (PR)
Task 5 (creating-custom-maps)│
Task 7 (CI: catalog)  ───────┘
Task 8 (Gemini visuals) ─────┘
```

**Parallel tracks:**
- **Track A:** Tasks 1-2 (schema) → Task 6 (CI validation)
- **Track B:** Tasks 3, 4, 5 (documentation) — all independent
- **Track C:** Task 7 (catalog CI + script)
- **Track D:** Task 8 (Gemini visuals)

Tasks 9 and 10 run after all tracks complete.
