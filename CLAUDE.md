# ATAK-Maps

Collection of MOBAC-format XML map source files for [ATAK](https://tak.gov). Each XML file points to an online tile server so ATAK can display and cache map imagery.

## Project Structure

```
<Provider>/              # e.g. Bing/, Google/, ESRI/, NAIP/, usgs/
  ├── map_name.xml       # Base map layers
GRG/
  ├── grg_*.xml          # Overlay layers
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
- **`customWmsMapSource`** — OGC Web Map Service sources (basemapDE, Canada, FEMA, Poland)
- **`customMultiLayerMapSource`** — Composite layers with per-layer opacity (not currently used in repo)

Schema at `schema/mobac-maps.xsd` validates all three types. Derived from ATAK's `MobacMapSourceFactory.java`.

## Conventions

- **One XML file per map layer** — no multi-source bundles
- **Directory = provider name** — group by tile source provider
- **Overlay prefix**: files in `GRG/` must start with `grg_`
- **Commits**: use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, etc.) — semantic-release parses these for versioning
- **No API keys in XML** — if a source requires auth, document it but don't commit secrets

## CI/CD

- **Validate Map XML** — validates all XML files against `schema/mobac-maps.xsd` on PRs and pushes to master
- **Map Release** — on push to master, zips all XML files and creates a GitHub Release via semantic-release
- **Update Map Catalog** — auto-generates the map catalog table in README.md when XML files change

## Reviewing PRs

When reviewing map contributions:
1. CI must pass — XML validates against the XSD schema
2. Verify the tile URL is accessible and returns valid tiles
3. Check zoom levels are reasonable for the source
4. Confirm the file is in the correct directory (base map vs overlay)
5. No API keys or tokens embedded in URLs
6. Uses conventional commit format (`feat: add <map name>`)
