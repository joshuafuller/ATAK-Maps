# ATAK-Maps

Collection of MOBAC-format XML map source files for [ATAK](https://tak.gov). Each XML file points to an online tile server so ATAK can display and cache map imagery.

## Project Structure

```text
maps/
  ├── base/<source>/<source>_<layer>.xml  # Base maps; <source> is lowercase: bing/, google/, de-basemap/, uk-os/
  ├── overlays/grg_<source>_<layer>.xml   # Transparent overlays ("+ " names)
  └── descriptions.yml   # Per map: category, text, test_point (keyed by slug)
schema/mobac-maps.xsd    # XSD schema — validates all XML map files
mapvalidator/            # ATAK harness, XML checks, explorer/README data, health issues
scripts/
  ├── gen_pages_catalog.py        # Explorer data, QR codes, hosted sources, data package
  ├── generate_readme_catalog.py  # README map list
  ├── make_readme_banner.py       # README banners from the brand SVGs
  └── site_check.py               # Built site in Chromium: JS errors, axe, explorer, overlaps
docs/                    # GitHub Pages site (MkDocs Material; theme in overrides/ + stylesheets/site.css)
  ├── index.md, install-guide.md ("Install & fix"), creating-custom-maps.md ("Add a map"), xml-reference.md
  ├── maps/index.html    # Map explorer (live Leaflet map); maps.js + health.js are generated
  └── assets/brand/      # Logo, mark, banners, contour art, illustrations
overrides/partials/      # Material header and named search dialog
.github/workflows/       # ci.yml (test, maps, site), pages, map-health-check, map-release, generate-catalog, super-linter, star-history
```

**Moving a map never changes its URL or slug.** The site serves each map at `/sources/<source>/<file>` (overlays: `/sources/GRG/<file>`) and its slug is `<source>-<stem>` (overlays: `grg-<stem>`), the same as before the `maps/` layout (`mapvalidator.catalog.site_path` / `map_slug`). tak:// links, printed QR codes, `descriptions.yml` keys and health records depend on them.

## XML Map Formats

Three root element types (see `docs/xml-reference.md` for full spec):

- **`customMapSource`** — TMS/XYZ tile sources (most files). Placeholders: `{$z}`, `{$x}`, `{$y}`, `{$q}` (quadkey), `{$serverpart}`
- **`customWmsMapSource`** — OGC Web Map Service sources (Canada, FEMA)
- **`customMultiLayerMapSource`** — Composite layers with per-layer opacity (e.g. `maps/base/blm/blm_satellite_ownership.xml`)

Schema at `schema/mobac-maps.xsd` validates all three types. Derived from ATAK's `MobacMapSourceFactory.java`.

## Conventions

- **One XML file per map layer** — no multi-source bundles
- **Directory = source name** — lowercase; non-US national agencies use `<country>-<agency>` (e.g. `de-basemap/`, `uk-os/`, `ca-nrcan/`)
- **Filenames**: lowercase `<source>_<layer>.xml` in `maps/base/<source>/`; overlays in `maps/overlays/` as `grg_<source>_<layer>.xml` (the prefix stops name clashes: ATAK imports every map into one folder)
- **Display `<name>`** — keep it short (about 20 characters; ATAK's layer list is narrow and sorts A–Z by name):
  - `<Source> <Layer>`, no ` - ` separator, no format/projection words (WMTS, 3857, EPSG): `Google Road`, `Esri Topo`, `USGS Imagery`
  - Non-US national maps start with the ISO country code: `DE Basemap Color`, `UK OS Road`, `CA Toporama`
  - Overlays start with `+` and a space: `+ Google Roads`, `+ FEMA Flood` (one-tap install puts overlays in the base map list, so the name must say it)
  - ATAK names the offline cache `<name>.sqlite`, so renaming a map starts it with an empty cache — avoid renames
- **Overlays** must be transparent PNG; opaque layers are base maps even if they look like "shading"
- **Commits**: use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, etc.) — semantic-release parses these for versioning
- **No API keys in XML** — if a source requires auth, document it but don't commit secrets
- **No hand-typed counts or versions** in README.md or the docs ("all 40 maps" goes stale). The map list in README.md is generated between the `MAP_CATALOG` markers by `mapvalidator.readme`; versions and status come from live badges. `tests/test_readme.py` fails on a typed map count

## CI/CD

- **CI** (`ci.yml`, every PR and push to master):
  - `test` — pytest with coverage ≥ 80%
  - `maps` — every map against `schema/mobac-maps.xsd`, the deep XML checks, and the ATAK harness on the maps a PR changes
  - `site` — builds the site and runs `scripts/site_check.py` (no JS errors, no axe violations, explorer loads, no overlapping map controls)
- **Map Release** — on push to master when maps change, zips `maps/` and creates a GitHub Release via semantic-release
- **Update Map Catalog** — regenerates the README map list (grouped by type, `mapvalidator.readme`) when XML files or `maps/descriptions.yml` change
- **Deploy Pages** — builds the site with the latest `map-health` artifact so the map explorer shows each map's status
- **Map Health Check** — weekly, runs the ATAK harness on every map: saves per-map health (`map-health` artifact), opens a "Map Health" issue for each failing map and closes it when the map works again, then rebuilds Pages

## ATAK harness

`uv run python -m mapvalidator --harness .` (or `--only <files>`) checks maps the way ATAK uses them:

- Builds the exact tile URL ATAK requests (`mapvalidator/atak_source.py`, ported from ATAK's `MobacMapSourceFactory`, `CustomMobacMapSource`, `CustomWmsMobacMapSource`) and fetches it with ATAK's User-Agent `TAK`
- Tests minZoom, maxZoom and maxZoom + 1 at the map's `test_point` (in `maps/descriptions.yml`; default New York)
- Fails on HTTP errors, OGC/HTML error bodies, known placeholder tiles, empty or blank base tiles, tiles blocked for `TAK`, opaque overlays, and broken naming rules
- Reports when the server has real tiles above maxZoom
- `--json <file>` also writes per-map health (`ok` / `warn` / `fail`, first problem, check time) keyed by catalog slug, for the site's map explorer

## Reviewing PRs

When reviewing map contributions:
1. CI must pass — XML validates against the XSD schema and the ATAK harness passes for the changed maps
2. Regional maps need a `test_point` in `maps/descriptions.yml`
3. Confirm the file is in the correct directory (base map vs overlay)
4. No API keys or tokens embedded in URLs
5. Uses conventional commit format (`feat: add <map name>`)
