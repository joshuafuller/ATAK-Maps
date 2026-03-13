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
