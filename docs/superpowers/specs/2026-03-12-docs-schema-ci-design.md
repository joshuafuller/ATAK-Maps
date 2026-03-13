# ATAK-Maps Documentation, Schema & CI/CD Overhaul

**Date:** 2026-03-12
**Status:** Approved
**Branch:** All work on a PR branch, no direct commits to master

## Problem

The ATAK-Maps repo has 36 XML map files across two distinct formats (`customMapSource` and `customWmsMapSource`), but documentation only covers the basic format. No formal XML schema exists anywhere — not from MOBAC, not from ATAK. CI only does generic XML linting. Users who want a subset of maps must download everything. Contributors adding WMS sources or using advanced features like `serverParts` have no reference.

## Goals

1. **User-focused install guide** — clear, visual, single ZIP download
2. **Contributor-focused XML reference** — complete spec for all 3 XML types, sourced from ATAK parser code
3. **XSD schema** — first formal MOBAC XML schema, used by CI for validation
4. **CI automation** — schema validation on PRs, auto-generated map catalog in README
5. **Visual documentation** — Gemini-generated diagrams for install flow, XML anatomy, directory layout

## Non-Goals

- Selective install script (future work)
- GitHub Pages site
- Migrating to TAK Streaming Tiles JSON format
- Tile URL liveness checking (future CI enhancement)

## Design

### Documentation Structure

```
docs/
├── install-guide.md            # Users: download, extract, install maps
├── xml-reference.md            # Contributors: complete MOBAC XML spec
├── creating-custom-maps.md     # Rewritten as quickstart, links to xml-reference
├── release-guide.md            # Existing, unchanged
└── images/
    ├── install-flow.png        # Gemini: download → extract → place → verify
    ├── xml-anatomy.png         # Gemini: annotated XML with callouts
    └── directory-layout.png    # Gemini: ATAK directory tree
```

#### install-guide.md

Target audience: ATAK users who want maps on their device.

Sections:
- **Quick Start** — download ZIP from Releases, extract, copy to device
- **Full Install** (all maps) — step-by-step with screenshots/diagrams
- **Selective Install** (per-provider ZIPs) — download only Bing, Google, etc.
- **Where Files Go** — `atak/imagery/mobile/mapsources/` and `atak/mobac/mapsources/` for base maps; `atak/grg/` for overlays
- **Base Maps vs Overlays** — what's the difference, how ATAK treats them
- **Verifying Installation** — how to confirm maps appear in ATAK
- **Offline Caching** — how ATAK caches tiles for offline use
- **Troubleshooting** — common issues (maps not appearing, blank tiles)

#### xml-reference.md

Target audience: contributors adding or modifying map sources.

Source of truth: ATAK's `MobacMapSourceFactory.java` parser.

Sections:
- **Overview** — three XML types, when to use each
- **`customMapSource`** — all elements, required/optional, defaults, validation rules
- **`customWmsMapSource`** — WMS-specific elements, version differences, CDATA usage
- **`customMultiLayerMapSource`** — composite layers, `layersAlpha` opacity control
- **URL Placeholders** — `{$z}`, `{$x}`, `{$y}`, `{$q}` (quadkey), `{$serverpart}`
- **Server Load Balancing** — `serverParts` with space-separated or comma-separated values
- **Coordinate Systems** — EPSG:3857 (default for TMS), EPSG:4326 (default for WMS)
- **Cache Control** — `tileUpdate` as millisecond TTL
- **Known Quirks** — `aditionalparameters` typo (accepted by parser), case sensitivity of `coordinatesystem` vs `coordinateSystem`
- **Element Reference Table** — quick-lookup table with element, type, default, required, description

#### creating-custom-maps.md (rewrite)

Becomes a quickstart/tutorial:
- Brief intro (3-5 paragraphs)
- "Create your first map source" walkthrough
- Link to xml-reference.md for full spec
- Link to install-guide.md for testing

### XSD Schema

Location: `schema/mobac-maps.xsd`

Derived from ATAK's `MobacMapSourceFactory.java` parser validation:

**customMapSource:**
- Required: `name` (string), `url` (string), `maxZoom` (non-negative int)
- Optional: `minZoom` (non-negative int, default 0), `tileType` (enum: png|jpg|PNG|JPG), `tileUpdate` (non-negative int), `serverParts` (string), `invertYCoordinate` (boolean), `backgroundColor` (pattern: `#[0-9A-Fa-f]{6}`), `coordinatesystem` (pattern: `EPSG:\d+`), `ignoreErrors` (boolean)

**customWmsMapSource:**
- Required: `name`, `url`, `layers`, `maxZoom`, `tileType`
- Optional: `minZoom`, `styles`, `version` (enum: 1.1.1|1.3.0|1.3.1), `coordinatesystem` (default EPSG:4326), `additionalparameters` OR `aditionalparameters`, `backgroundColor`, `north`/`south`/`east`/`west` (decimal), `tileUpdate`

**customMultiLayerMapSource:**
- Required: `name`, `layers` (container for nested sources)
- Optional: `backgroundColor`, `layersAlpha` (space-separated decimals 0.0-1.0)

Schema uses `xs:choice` for the root element to support all three types.

### CI/CD Workflows

#### 1. `validate-maps.yml` (new)

Trigger: PRs + push to master (XML file changes)

Steps:
1. Checkout repo
2. Install `libxml2-utils` (for `xmllint`)
3. Run `xmllint --schema schema/mobac-maps.xsd` against every XML file
4. Report failures with specific element/line info

Replaces the generic super-linter XML validation with schema-aware validation.

#### 2. `map-release.yml` (unchanged)

Existing workflow kept as-is — builds single `atak-maps.zip` with all XML files.

#### 3. `generate-catalog.yml` (new)

Trigger: push to master (XML changes)

Steps:
1. Parse every XML file with a shell script or Python
2. Extract: provider (directory), name, minZoom, maxZoom, tileType, source type (TMS/WMS/Multi)
3. Generate markdown table sorted by provider
4. Insert/replace the `## Map Catalog` section in README.md
5. Commit updated README back to master

The catalog table format:

| Provider | Map Name | Zoom | Source Type | Tile Format |
|----------|----------|------|-------------|-------------|
| Bing | Bing - Satellite | 0-20 | TMS | jpg |

### Visuals (Gemini MCP)

Three images generated via `mcp__gemini-image__gemini_generate_image`:

1. **install-flow.png** — flowchart showing: GitHub Releases → Download ZIP → Extract → Copy XML files to ATAK directories → Open ATAK → Select map layer
2. **xml-anatomy.png** — annotated `customMapSource` XML with labeled callouts for each element explaining its purpose
3. **directory-layout.png** — ATAK device directory tree highlighting where base maps and overlays go

Style: clean, technical, dark background suitable for GitHub markdown rendering.

### CLAUDE.md Update

Update the existing CLAUDE.md to reflect:
- New docs structure
- Schema location and purpose
- Updated CI/CD pipeline descriptions
- PR review checklist updated with schema validation

## Implementation Order

1. Create feature branch
2. XSD schema (unlocks CI validation)
3. xml-reference.md (most complex doc, depends on schema decisions)
4. install-guide.md (user-facing)
5. creating-custom-maps.md rewrite
6. CI workflows (validate, enhanced release, catalog generator)
7. Gemini visuals
8. CLAUDE.md + README.md updates
9. Open PR

Steps 2-5 can be parallelized with agent teams. Step 6 depends on schema (step 2). Step 7 can run in parallel with step 6.

## Source of Truth

All XML element definitions sourced from:
- `atak-civ-client/takkernel/engine/src/main/java/com/atakmap/map/layer/raster/mobac/MobacMapSourceFactory.java`
- `atak-civ-client/takkernel/engine/src/main/java/com/atakmap/map/layer/raster/mobac/CustomMobacMapSource.java`
- `atak-civ-client/takkernel/engine/src/main/java/com/atakmap/map/layer/raster/mobac/CustomWmsMobacMapSource.java`
- `atak-civ-client/takkernel/engine/src/main/java/com/atakmap/map/layer/raster/mobac/CustomMultiLayerMobacMapSource.java`
- `atak-civ-client/ATAK_Supported_Map_Types.md`

ATAK scan directories for MOBAC sources:
- `/atak/imagery/mobile/mapsources/`
- `/atak/mobac/mapsources/`
