# ATAK-Maps

Collection of MOBAC-format XML map source files for [ATAK](https://tak.gov). Each XML file points to an online tile server so ATAK can display and cache map imagery.

## Project Structure

```
<Provider>/           # e.g. Bing/, Google/, ESRI/, NAIP/, usgs/
  ├── map_name.xml    # Base map layers → install to ATAK/imagery/
GRG/
  ├── grg_*.xml       # Overlay layers → install to ATAK/grg/
docs/                 # Guides (custom maps, releases)
images/               # Logo and screenshots
.github/workflows/    # CI: XML linting + semantic-release
```

## XML Map Format (MOBAC)

Every map file follows this structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
  <name>Human-readable name</name>
  <minZoom>0</minZoom>
  <maxZoom>20</maxZoom>
  <tileType>png</tileType>
  <tileUpdate>None</tileUpdate>
  <url>https://tile-server/{$z}/{$x}/{$y}.png</url>
  <backgroundColor>#000000</backgroundColor>
</customMapSource>
```

- `{$z}`, `{$x}`, `{$y}` — standard TMS/slippy map placeholders
- `{$q}` — quadkey (used by Bing)
- Overlays (GRG dir) use prefix `grg_` in filename

## Conventions

- **One XML file per map layer** — no multi-source bundles
- **Directory = provider name** — group by tile source provider
- **Overlay prefix**: files in `GRG/` must start with `grg_`
- **Commits**: use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, etc.) — semantic-release parses these for versioning
- **No API keys in XML** — if a source requires auth, document it but don't commit secrets

## CI/CD

- **Lint XML Maps** — runs `super-linter` on changed XML files (PRs + pushes to master)
- **Map Release** — on push to master, zips all XML files and creates a GitHub Release via semantic-release

## Reviewing PRs

When reviewing map contributions:
1. Verify the tile URL is accessible and returns valid tiles
2. Check zoom levels are reasonable for the source
3. Ensure the XML is well-formed
4. Confirm the file is in the correct directory (base map vs overlay)
5. No API keys or tokens embedded in URLs
