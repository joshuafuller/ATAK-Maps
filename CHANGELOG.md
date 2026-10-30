## [2.0.0](https://github.com/joshuafuller/ATAK-Maps/compare/v1.11.0...v2.0.0) (2026-10-30)

### ⚠ BREAKING CHANGES

* **release:** every map file and display name changed in v1.10.1 (#100). ATAK keys offline caches by map name, so old <name>.sqlite caches are orphaned; re-download offline tiles.

### Bug Fixes

* **release:** breaking commits make a major release ([#102](https://github.com/joshuafuller/ATAK-Maps/issues/102)) ([7e9e918](https://github.com/joshuafuller/ATAK-Maps/commit/7e9e9189c972d2966204b0e986e32c9d331d0064))

# [1.11.0](https://github.com/joshuafuller/ATAK-Maps/compare/v1.10.1...v1.11.0) (2026-10-30)


### Features

* **validator:** ATAK harness that tests maps exactly as ATAK fetches them ([#101](https://github.com/joshuafuller/ATAK-Maps/issues/101)) ([ac29eda](https://github.com/joshuafuller/ATAK-Maps/commit/ac29eda62ca0d26b3cb68dc27b0044840008dda1))

## [1.10.1](https://github.com/joshuafuller/ATAK-Maps/compare/v1.10.0...v1.10.1) (2026-10-30)


* refactor!: rename all maps to short names and fix broken sources ([#100](https://github.com/joshuafuller/ATAK-Maps/issues/100)) ([81bded0](https://github.com/joshuafuller/ATAK-Maps/commit/81bded019d027ebc8d1bccef35aea847fe1257e1))


### BREAKING CHANGES

* every map file and display name changed. Old offline caches (<name>.sqlite) are orphaned; re-download tiles after updating.

# [1.10.0](https://github.com/joshuafuller/ATAK-Maps/compare/v1.9.0...v1.10.0) (2026-10-30)


### Features

* **google:** add hybrid no-POI, bike and transit layers; short clear names ([#97](https://github.com/joshuafuller/ATAK-Maps/issues/97)) ([843d54b](https://github.com/joshuafuller/ATAK-Maps/commit/843d54bfb5c51ebf79e8e820c2df97d08e459ba8))

# [1.9.0](https://github.com/joshuafuller/ATAK-Maps/compare/v1.8.0...v1.9.0) (2026-10-13)


### Bug Fixes

* import per-map XML from GitHub Pages (application/xml), not raw ([#85](https://github.com/joshuafuller/ATAK-Maps/issues/85)) ([2a0c4af](https://github.com/joshuafuller/ATAK-Maps/commit/2a0c4afdc16fc43c007b590eae9ed9fab6452dc2))
* **security:** update docs dependency and reporting policy ([#95](https://github.com/joshuafuller/ATAK-Maps/issues/95)) ([d610afd](https://github.com/joshuafuller/ATAK-Maps/commit/d610afd941539f5a2bb4deafa0518367658192b6))
* **ui:** tap-to-enlarge QR lightbox; bigger scannable README QR ([#89](https://github.com/joshuafuller/ATAK-Maps/issues/89)) ([93c6cf2](https://github.com/joshuafuller/ATAK-Maps/commit/93c6cf2a45609b2e275e07270113277faa1d591d))
* update OpenSeaMap endpoints and document map tips ([df4ff0f](https://github.com/joshuafuller/ATAK-Maps/commit/df4ff0f2120ca48ca046c8983d4e60b517cbfafe))
* Updated basemapDE to use a WMTS service ([#93](https://github.com/joshuafuller/ATAK-Maps/issues/93)) ([5e5cca0](https://github.com/joshuafuller/ATAK-Maps/commit/5e5cca0e4a84e9da8d2c4f64865df8e73d1b0483))


### Features

* bundle all maps as an importable ATAK data package ([#86](https://github.com/joshuafuller/ATAK-Maps/issues/86)) ([c71a2ff](https://github.com/joshuafuller/ATAK-Maps/commit/c71a2ff97bc77a7274457c99a8195632a9f8cfa2))
* redesign the Maps catalog, landing page, and README ([#88](https://github.com/joshuafuller/ATAK-Maps/issues/88)) ([83f56ee](https://github.com/joshuafuller/ATAK-Maps/commit/83f56eeb8d65c03f33a1094c726e584f7d7fdcab))

# [1.8.0](https://github.com/joshuafuller/ATAK-Maps/compare/v1.7.1...v1.8.0) (2026-07-13)


### Bug Fixes

* **bc-wildfire:** conform merged source to schema and conventions ([#82](https://github.com/joshuafuller/ATAK-Maps/issues/82)) ([767d630](https://github.com/joshuafuller/ATAK-Maps/commit/767d630970780ec567d5dfe6914a095f5a1bee06)), closes [#76](https://github.com/joshuafuller/ATAK-Maps/issues/76)


### Features

* add BC Wildfire Overlay source ([#76](https://github.com/joshuafuller/ATAK-Maps/issues/76)) ([d6c4bf9](https://github.com/joshuafuller/ATAK-Maps/commit/d6c4bf9f40ced3fbda8aefd0675c91a47dee93c9))
* add BLM land ownership (SMA) map sources ([#80](https://github.com/joshuafuller/ATAK-Maps/issues/80)) ([39b2eda](https://github.com/joshuafuller/ATAK-Maps/commit/39b2edaf4ddb426c4e6df3484f493e7338db49b1))
* add Ordnance Survey map layers (Great Britain) ([#83](https://github.com/joshuafuller/ATAK-Maps/issues/83)) ([ddba21d](https://github.com/joshuafuller/ATAK-Maps/commit/ddba21d0d664ede6552b6b97edcaf9a0a4de674a)), closes [#68](https://github.com/joshuafuller/ATAK-Maps/issues/68)
* GitHub Pages site with per-map QR codes and Add-to-ATAK ([#84](https://github.com/joshuafuller/ATAK-Maps/issues/84)) ([4935b03](https://github.com/joshuafuller/ATAK-Maps/commit/4935b0335a92c69643d7b9367d7a0e7cd55c65bf)), closes [#81](https://github.com/joshuafuller/ATAK-Maps/issues/81)

## [1.7.1](https://github.com/joshuafuller/ATAK-Maps/compare/v1.7.0...v1.7.1) (2026-03-13)


### Bug Fixes

* **ci:** checkout latest master tip in release workflow ([330f36c](https://github.com/joshuafuller/ATAK-Maps/commit/330f36c0d19a6a568dc3745cbd4f4ce4e023e682))

# [1.7.0](https://github.com/joshuafuller/ATAK-Maps/compare/v1.6.0...v1.7.0) (2026-03-13)


### Bug Fixes

* address linter failures and Copilot review feedback ([d4252c6](https://github.com/joshuafuller/ATAK-Maps/commit/d4252c6dbe090a9000991653b2c797b1499573fb))
* correct XML issues found by mapvalidator ([fd779db](https://github.com/joshuafuller/ATAK-Maps/commit/fd779dbfb7786d3f83fd2f640b3a130a5f8eb5cc))
* disable isort in super-linter, keep black for formatting ([42173d4](https://github.com/joshuafuller/ATAK-Maps/commit/42173d411672f98bf1f88bd952663013b72cd63c))
* disable JSCPD and configure isort in super-linter ([53f2c04](https://github.com/joshuafuller/ATAK-Maps/commit/53f2c0496b9079e60f984cd76a96291cae411cf8))
* resolve remaining CI lint failures ([cd6b43d](https://github.com/joshuafuller/ATAK-Maps/commit/cd6b43d1ea80857e6c0ce545b6d4c64f36f8eb85))


### Features

* add CI workflows for mapvalidator, remove standalone script ([f78a785](https://github.com/joshuafuller/ATAK-Maps/commit/f78a785dc4e78add8a185605fbd198cb50e17e70))
* add deep validation script with liveness probing ([3675175](https://github.com/joshuafuller/ATAK-Maps/commit/3675175f013fdd4c2dd32a384d513e5d096e54c3))
* add map validation & liveness monitoring ([#70](https://github.com/joshuafuller/ATAK-Maps/issues/70)) ([974c2a1](https://github.com/joshuafuller/ATAK-Maps/commit/974c2a1ccb606a40fddc82fb6851de6244a28f93))
* add mapvalidator package with deep XML validation and liveness probing ([185a8eb](https://github.com/joshuafuller/ATAK-Maps/commit/185a8eb9757d09db1b98aaaf3a37ba89fbc7677c))
* add soft-block detection, multi-region probing, and remove dead map sources ([66be333](https://github.com/joshuafuller/ATAK-Maps/commit/66be3339976b399b9b65546beb8eb485b1fe8661))

# [1.6.0](https://github.com/joshuafuller/ATAK-Maps/compare/v1.5.0...v1.6.0) (2026-03-13)


### Bug Fixes

* address PR review comments ([537b23d](https://github.com/joshuafuller/ATAK-Maps/commit/537b23df6af0ee55ffca0e26a6314245d7708ade))
* rename basemapDE files to remove spaces in filenames ([8d23b1e](https://github.com/joshuafuller/ATAK-Maps/commit/8d23b1ebd3117cdccd07eacc7619fd1d3c0c24d0))


### Features

* add XSD schema for MOBAC XML map validation ([9da31a9](https://github.com/joshuafuller/ATAK-Maps/commit/9da31a993c14da2fe7e741d5fa67d743ab486516))

# Changelog

## [1.5.0](https://github.com/joshuafuller/ATAK-Maps/compare/v1.4.1...v1.5.0) (2025-10-02)

### Features

* add Bing Satellite (aerial-only) map source ([#67](https://github.com/joshuafuller/ATAK-Maps/issues/67)) ([433733e](https://github.com/joshuafuller/ATAK-Maps/commit/433733e9fb161b32cd48ac1cfe6eb9b7c02b8386)), closes [#64](https://github.com/joshuafuller/ATAK-Maps/issues/64)

## [1.4.1](https://github.com/joshuafuller/ATAK-Maps/compare/v1.4.0...v1.4.1) (2025-05-20)

### Bug Fixes

* minor update to force a release ([5a388b8](https://github.com/joshuafuller/ATAK-Maps/commit/5a388b8))
* Update asset label in semantic-release configuration ([5f17164](https://github.com/joshuafuller/ATAK-Maps/commit/5f17164))

## [1.4.0](https://github.com/joshuafuller/ATAK-Maps/compare/v1.3.0...v1.4.0) (2025-05-20)

### Features

* BasemapDE - German government topographical map ([#59](https://github.com/joshuafuller/ATAK-Maps/issues/59)) ([040798a](https://github.com/joshuafuller/ATAK-Maps/commit/040798a))

### Bug Fixes

* Simplify semantic-release configuration ([7d7c60e](https://github.com/joshuafuller/ATAK-Maps/commit/7d7c60e))

## [1.3.0](https://github.com/joshuafuller/ATAK-Maps/compare/v1.2.1...v1.3.0) (2025-05-20)

### Features

* Remove broken FEMA NFHL XML layers and introduce new Flood Hazard Zones WMS configuration ([f4d5535](https://github.com/joshuafuller/ATAK-Maps/commit/f4d5535))
* Adding Polish Ortho Maps ([a889bc8](https://github.com/joshuafuller/ATAK-Maps/commit/a889bc8))

### Bug Fixes

* Update semantic-release configuration to rename ZIP files dynamically ([ca2be44](https://github.com/joshuafuller/ATAK-Maps/commit/ca2be44))
* Remove redundant comment in PL Geoportal Ortofoto EPSG3857 XML configuration ([f983afc](https://github.com/joshuafuller/ATAK-Maps/commit/f983afc))

## [1.2.1](https://github.com/joshuafuller/ATAK-Maps/compare/v1.2.0...v1.2.1) (2025-05-17)

### Bug Fixes

* clarify docs phrasing ([#50](https://github.com/joshuafuller/ATAK-Maps/issues/50)) ([d317f2e](https://github.com/joshuafuller/ATAK-Maps/commit/d317f2e722a202a25877c9ce0c17251e7f3cb240))
