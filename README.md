<div align="center">

<img src="https://github.com/joshuafuller/ATAK-Maps/blob/master/images/ATAK_MAPS_Logo.png?raw=true" alt="ATAK-Maps" width="440">

# ATAK-Maps

**Install any map into [ATAK](https://tak.gov) in one tap.**

A curated, open collection of **40** satellite, topographic, nautical, trail and
overlay map sources — scan a QR, tap **Add to ATAK**, or side-load. No manual
file wrangling. ATAK&nbsp;5.1+.

[![Latest Release](https://img.shields.io/github/v/release/joshuafuller/ATAK-Maps?style=flat)](https://github.com/joshuafuller/ATAK-Maps/releases/latest) ![Release Date](https://img.shields.io/github/release-date/joshuafuller/ATAK-Maps?style=flat) [![Downloads](https://img.shields.io/github/downloads/joshuafuller/ATAK-Maps/total?style=flat)](https://github.com/joshuafuller/ATAK-Maps/releases/latest) [![XML Validation](https://img.shields.io/github/actions/workflow/status/joshuafuller/ATAK-Maps/validate-maps.yml?label=XML%20validation&style=flat)](https://github.com/joshuafuller/ATAK-Maps/actions/workflows/validate-maps.yml)
[![Stars](https://img.shields.io/github/stars/joshuafuller/ATAK-Maps?style=flat)](https://github.com/joshuafuller/ATAK-Maps/stargazers) [![License](https://img.shields.io/github/license/joshuafuller/ATAK-Maps?style=flat)](LICENSE) [![Discord](https://img.shields.io/discord/698067185515495436?style=flat)](https://discord.gg/dQUYADMW87) [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/joshuafuller/ATAK-Maps)

### [Browse &amp; install from the catalog site&nbsp;&rarr;](https://joshuafuller.github.io/ATAK-Maps/)

</div>

## Add to ATAK

<table>
<tr>
<td width="260" align="center">
<img src="images/add-to-atak.png" width="240" alt="QR code to add all maps to ATAK"><br>
<sub>Scan to add all 40 maps</sub>
</td>
<td>

**Fastest — per map:** open the **[catalog site](https://joshuafuller.github.io/ATAK-Maps/maps/)**
on your ATAK device and tap **Add to ATAK** on any map (filter by style, or
scan a QR from another screen).

**Whole set at once:** scan the QR, or on the device paste this into a browser —
it imports a data package with all 40 maps, kept in ATAK's Mission Package Tool
so you can remove them later:

`tak://com.atakmap.app/import?url=https%3A%2F%2Fjoshuafuller.github.io%2FATAK-Maps%2Fpack%2Fatak-maps-all.zip`

**Manual:** download the latest `atak-maps.zip` from the
[Releases page](https://github.com/joshuafuller/ATAK-Maps/releases) and open it
with ATAK's Import feature. See the **[Install Guide](docs/install-guide.md)**
for troubleshooting and offline caching.

</td>
</tr>
</table>

> Requires ATAK 5.1+ (the version that added the `tak://` import scheme). GitHub
> can't render a tappable `tak://` link here — use the QR or the catalog site,
> where the buttons are tappable on-device.

## What is ATAK-Maps?

A collection of [MOBAC-format](https://mobac.sourceforge.io/) XML files, each a
pointer to an online map/imagery source. [ATAK](https://tak.gov) reads them to
display live imagery and **cache map areas for offline use** — essential where
connectivity is limited. Pick a region and quality, and ATAK downloads it for
the field. (Not affiliated with TAK.GOV.)

## Map Catalog

All available map layers, auto-generated from the XML files in this repository:

<!-- MAP_CATALOG_START -->

| Provider | Map Name | Zoom (min–max) | Tile Type | Source |
|----------|----------|----------------|-----------|--------|
| basemapDE | basemap.de Raster, Farbe | 0–19 | PNG | WMS |
| basemapDE | basemap.de Raster, grau | 0–19 | PNG | WMS |
| Bing | Bing - Hybrid | 0–20 | png | TMS |
| Bing | Bing - Maps | 0–20 | png | TMS |
| Bing | Bing - Satellite | 0–20 | jpg | TMS |
| BLM | BLM - Land Ownership (SMA) | 1–14 | jpg | TMS |
| BLM | BLM - Satellite + Land Ownership | —–— | — | Multi-Layer |
| cycleosm | CycleOSM - OSM Cycle | 0–21 | png | TMS |
| ESRI | Esri - Clarity | 1–20 | jpg | TMS |
| ESRI | Esri - Nat Geo World | 1–20 | jpg | TMS |
| ESRI | Esri - USA Topo Maps | 0–15 | png | TMS |
| ESRI | Esri - World Topo | 1–20 | jpg | TMS |
| Google | Google - Hybrid | 0–20 | jpg | TMS |
| Google | Google - Roadmap Alt | 0–20 | jpg | TMS |
| Google | Google - Roadmap No Poi | 0–20 | jpg | TMS |
| Google | Google - Roadmap Standard | 0–20 | jpg | TMS |
| Google | Google - Satellite Only | 0–20 | jpg | TMS |
| Google | Google - Terrain | 0–20 | jpg | TMS |
| GRG | BC Wildfire - Fire Perimeters (Current) | 0–22 | png | WMS |
| GRG | FEMA NFHL - Flood Hazard Zones (WMS) | 5–19 | PNG | WMS |
| GRG | GRG - BLM Public Lands Overlay | 1–14 | png | TMS |
| GRG | GRG - Google Road Only Overlay | 0–20 | jpg | TMS |
| GRG | GRG - Google Terrain Shading Overlay | 0–20 | jpg | TMS |
| GRG | GRG - WaymarkedTrails Cycle Routes Overlay | 0–18 | png | TMS |
| michelin | Michelin - OSM Michelin | 5–19 | — | TMS |
| mtbmapcz | MTBMap.cz - MTB Map Europe | 0–21 | png | TMS |
| NAIP | NAIP – USDA CONUS Prime | 0–17 | jpg | TMS |
| NaturalResourcesCanada | Canada - Toporama | 0–23 | jpg | WMS |
| NaturalResourcesCanada | Canada Base Map – Transportation | 0–23 | jpg | WMS |
| openseamap | OpenSeaMap – Base Chart | 0–18 | png | TMS |
| openseamap | OpenSeaMap – Seamarks | 0–18 | png | TMS |
| opentopo | OpenTopo - Opentopomap | 1–17 | png | TMS |
| OrdnanceSurvey | OS - Light 3857 | 0–16 | png | TMS |
| OrdnanceSurvey | OS - Outdoor 3857 | 0–16 | png | TMS |
| OrdnanceSurvey | OS - Road 3857 | 0–16 | png | TMS |
| Poland | PL Ortofoto Std (WMTS EPSG3857) | 0–20 | JPG | TMS |
| usgs | USGS - Usgsbasemap | 0–15 | png | TMS |
| usgs | USGS - Usgsimageryonly | 0–15 | png | TMS |
| usgs | USGS - Usgsimagerytopo | 0–15 | png | TMS |
| usgs | USGS - Usgsshadedrelief | 0–15 | png | TMS |

<!-- MAP_CATALOG_END -->

## Frequently Asked Questions (FAQ)

- **Can I cache these maps for offline use?** Yes, ATAK supports automatic and manual caching of maps.
- **Will more maps be added?** We continuously update our map collection. Share your suggestions [here](https://github.com/joshuafuller/ATAK-Maps/issues).

## OpenStreetMap Compatibility

Please note that OpenStreetMap may restrict ATAK client access. These maps are included for reference, and we're exploring solutions.

## Creating Custom Maps

Want to add your own map sources? See the [Creating Custom Maps quickstart](docs/creating-custom-maps.md) to get started, or the [MOBAC XML Reference](docs/xml-reference.md) for the complete specification.

## Contributing

We welcome your contributions! Review our [contribution guidelines](CONTRIBUTING.md) for more information.

## Support

Join our [Discord server](https://discord.gg/dQUYADMW87) for support and community engagement.

## Publishing a New Version

To publish a new release, push a commit to `master` with a message that begins
with `feat:` or `fix:` using the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format.
The *Map Release* workflow runs automatically on those commits—or it can be
triggered manually from the *Actions* tab—and uses semantic-release to tag the
commit and upload `atak-maps.zip`.
For more details, including instructions for forks, see [docs/release-guide.md](docs/release-guide.md).

## License

ATAK-Maps is distributed under the [MIT License](LICENSE).

## Stargazers over time
[![Stargazers over time](https://starchart.cc/joshuafuller/ATAK-Maps.svg?variant=adaptive)](https://starchart.cc/joshuafuller/ATAK-Maps)


