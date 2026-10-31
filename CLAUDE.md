# ATAK-Maps

Collection of MOBAC-format XML map source files for [ATAK](https://tak.gov). Each XML file points to an online tile server so ATAK can display and cache map imagery.

## Project Structure

```text
<source>/                # lowercase: bing/, google/, esri/, usgs/, de-basemap/, uk-os/
  ├── <source>_<layer>.xml   # Base map layers
GRG/
  ├── grg_<source>_<layer>.xml  # Overlay layers (transparent)
schema/
  └── mobac-maps.xsd     # XSD schema — validates all XML map files
docs/
  ├── install-guide.md   # User-focused installation guide
  ├── xml-reference.md   # Complete MOBAC XML spec (from ATAK source)
  ├── creating-custom-maps.md  # Quickstart tutorial for contributors
  ├── release-guide.md   # Release process
  └── images/            # Diagrams (install flow, XML anatomy, directory layout)
.github/
  ├── workflows/
  │   ├── validate-maps.yml    # XSD schema validation on PRs
  │   ├── generate-catalog.yml # Auto-generates map catalog in README
  │   ├── map-release.yml      # Semantic-release + ZIP
  │   └── super-linter.yml     # Non-XML linting
  └── scripts/
      └── generate-catalog.py  # Parses XML → README catalog table
```

## XML Map Formats

Three root element types (see `docs/xml-reference.md` for full spec):

- **`customMapSource`** — TMS/XYZ tile sources (most files). Placeholders: `{$z}`, `{$x}`, `{$y}`, `{$q}` (quadkey), `{$serverpart}`
- **`customWmsMapSource`** — OGC Web Map Service sources (Canada, FEMA)
- **`customMultiLayerMapSource`** — Composite layers with per-layer opacity (e.g. `blm/blm_satellite_ownership.xml`)

Schema at `schema/mobac-maps.xsd` validates all three types. Derived from ATAK's `MobacMapSourceFactory.java`.

## Conventions

- **One XML file per map layer** — no multi-source bundles
- **Directory = source name** — lowercase; non-US national agencies use `<country>-<agency>` (e.g. `de-basemap/`, `uk-os/`, `ca-nrcan/`)
- **Filenames**: lowercase `<source>_<layer>.xml`; overlays live in `GRG/` as `grg_<source>_<layer>.xml`
- **Display `<name>`** — keep it short (about 20 characters; ATAK's layer list is narrow and sorts A–Z by name):
  - `<Source> <Layer>`, no ` - ` separator, no format/projection words (WMTS, 3857, EPSG): `Google Road`, `Esri Topo`, `USGS Imagery`
  - Non-US national maps start with the ISO country code: `DE Basemap Color`, `UK OS Road`, `CA Toporama`
  - Overlays start with `+` and a space: `+ Google Roads`, `+ FEMA Flood` (one-tap install puts overlays in the base map list, so the name must say it)
  - ATAK names the offline cache `<name>.sqlite`, so renaming a map starts it with an empty cache — avoid renames
- **Overlays** must be transparent PNG; opaque layers are base maps even if they look like "shading"
- **Commits**: use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, etc.) — semantic-release parses these for versioning
- **No API keys in XML** — if a source requires auth, document it but don't commit secrets

## CI/CD

- **Validate Map XML** — validates all XML files against `schema/mobac-maps.xsd` on PRs and pushes to master
- **Map Release** — on push to master, zips all XML files and creates a GitHub Release via semantic-release
- **Update Map Catalog** — auto-generates the map catalog table in README.md when XML files change
- **Deep Map Validation** — on PRs, runs the ATAK harness on the changed maps
- **Map Health Check** — weekly, runs the ATAK harness on every map, saves per-map health (`map-health` artifact) and rebuilds Pages

## ATAK harness

`uv run python -m mapvalidator --harness .` (or `--only <files>`) checks maps the way ATAK uses them:

- Builds the exact tile URL ATAK requests (`mapvalidator/atak_source.py`, ported from ATAK's `MobacMapSourceFactory`, `CustomMobacMapSource`, `CustomWmsMobacMapSource`) and fetches it with ATAK's User-Agent `TAK`
- Tests minZoom, maxZoom and maxZoom + 1 at the map's `test_point` (in `descriptions.yml`; default New York)
- Fails on HTTP errors, OGC/HTML error bodies, known placeholder tiles, empty or blank base tiles, tiles blocked for `TAK`, opaque overlays, and broken naming rules
- Reports when the server has real tiles above maxZoom
- `--json <file>` also writes per-map health (`ok` / `warn` / `fail`, first problem, check time) keyed by catalog slug, for the site's map explorer

## Reviewing PRs

When reviewing map contributions:
1. CI must pass — XML validates against the XSD schema and the ATAK harness passes for the changed maps
2. Regional maps need a `test_point` in `descriptions.yml`
3. Confirm the file is in the correct directory (base map vs overlay)
4. No API keys or tokens embedded in URLs
5. Uses conventional commit format (`feat: add <map name>`)
