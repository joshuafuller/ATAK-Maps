# ATAK-Maps

![ATAK-Maps Logo](https://github.com/joshuafuller/ATAK-Maps/blob/master/images/ATAK_MAPS_Logo.png?raw=true)

![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/joshuafuller/ATAK-Maps) ![GitHub Release Date](https://img.shields.io/github/release-date/joshuafuller/ATAK-Maps?style=flat)
![GitHub All Releases](https://img.shields.io/github/downloads/joshuafuller/ATAK-Maps/total?style=flat) [![Discord](https://img.shields.io/discord/698067185515495436?style=flat)](https://discord.gg/dQUYADMW87) [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/joshuafuller/ATAK-Maps)

## Detailed Overview of ATAK-Maps

ATAK-Maps is a comprehensive collection of XML files, formatted in the Mobile Atlas Creator (MOBAC) format. This format is used in [Android Tactical Assault Kit (ATAK)](https://tak.gov), an advanced geospatial mapping tool employed in various sectors including military, law enforcement, and emergency services. This repository and its contents are not affiliated with TAK.GOV in any way.

### What are ATAK-Maps?

These XML files in ATAK-Maps act as pointers or references to a multitude of online map sources. By using these files, ATAK can seamlessly access and display current and relevant map imagery from these sources. This capability is vital for operations requiring up-to-date geospatial information.

### MOBAC Format

The MOBAC format is integral to the functionality of ATAK-Maps. It enables the definition of how ATAK accesses these online map sources. For more detailed information on the MOBAC format, visit [Mobile Atlas Creator](https://mobac.sourceforge.io/).

### Usage and Functionality

- **Dynamic Map Access**: ATAK-Maps facilitates the dynamic access of various map sources, ensuring that users have the most current imagery available for their operational needs.
- **Offline Caching**: One of the key features of ATAK is its ability to cache these maps. With ATAK-Maps, users can download and store map areas for offline use, which is crucial in environments with limited or no internet access.
- **Customization and Selection**: Users can also select specific areas and set the desired image quality for downloads, allowing for tailored map coverage based on operational requirements.

## Installation Guide

1. **Download** `ATAK-Maps.zip` from the [Releases page](https://github.com/joshuafuller/ATAK-Maps/releases).
2. **Extract** the ZIP contents.
3. **Copy** base map XMLs to `atak/imagery/mobile/mapsources/` on your device.
4. **Copy** overlay XMLs (prefixed `grg_`) to `atak/grg/`.
5. **Verify** the new maps appear in ATAK's map layer selector.

For detailed instructions, troubleshooting, and offline caching, see the **[Install Guide](docs/install-guide.md)**.

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
| GRG | FEMA NFHL - Flood Hazard Zones (WMS) | 5–19 | PNG | WMS |
| GRG | GRG - Google Road Only Overlay | 0–20 | jpg | TMS |
| GRG | GRG - Google Terrain Shading Overlay | 0–20 | jpg | TMS |
| GRG | GRG - USDA Fstopo Overlay | 0–17 | png | TMS |
| GRG | GRG - WaymarkedTrails Cycle Routes Overlay | 0–18 | png | TMS |
| michelin | Michelin - OSM Michelin | 0–19 | — | TMS |
| mtbmapcz | MTBMap.cz - MTB Map Europe | 0–21 | png | TMS |
| NAIP | NAIP – USDA CONUS Prime | 0–17 | jpg | TMS |
| NAIP | NAIP – USGS National Map | 0–17 | jpg | TMS |
| NationalLandSurveyOfFinland | National Land Survey of Finland - MML | 2–19 | jpg | TMS |
| NaturalResourcesCanada | Canada - Toporama | 0–23 | jpg | WMS |
| NaturalResourcesCanada | Canada Base Map – Transportation | 0–23 | jpg | WMS |
| openseamap | OpenSeaMap – Base Chart | 0–18 | png | TMS |
| openseamap | OpenSeaMap – Seamarks | 0–18 | png | TMS |
| opentopo | OpenTopo - Opentopomap | 1–17 | png | TMS |
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


