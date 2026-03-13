# Map Validation & Liveness Monitoring — Design Spec

**Date:** 2026-03-13
**Branch:** `feature/map-liveness-checks`
**Audience:** Maintainer + contributors (fast PR feedback + ongoing monitoring)

## Problem

The ATAK-Maps repository has 36 XML map source files with no validation beyond basic XSD schema checks. The schema only validates structure — it can't catch:

- Inverted zoom ranges, unreasonable maxZoom values
- Dead tile servers, DNS failures
- Servers that block ATAK's `TAK` user-agent (e.g., OpenStreetMap)
- Wrong element casing that ATAK's parser silently ignores
- HTTP URLs where HTTPS is available
- Malformed serverParts, missing URL placeholders

Known issues found during initial analysis:
- 10 files use insecure HTTP
- 2 files use camelCase `coordinateSystem` (ATAK only reads lowercase)
- 2 files have comma-separated serverParts (should be space-separated)
- 1 dead DNS (Finland — `tiles.kartat.kapsi.fi`)
- 2 Canadian maps with maxZoom=23 (exceeds typical ceiling)
- Several servers returning 404/500

## Goals

1. A Python validation library that catches every issue XSD cannot express
2. Dual user-agent liveness probing (TAK vs generic) to detect ATAK-specific blocks
3. TDD test suite with 80%+ coverage, using real XML fixtures and the `responses` library for HTTP mocking
4. Automated weekly monitoring with GitHub issue creation for failures
5. Fast PR feedback for contributors on XML quality

## Prior Art

The existing `.github/scripts/validate-maps-deep.py` (346 lines, added on this branch) is a standalone script
implementing filename checks, zoom validation, URL placeholder checks, WMS checks, duplicate detection,
and basic single-UA liveness probing. It will be **refactored into the `mapvalidator/` package** — the logic
is reused, not rewritten. Once the package is complete, `validate-maps-deep.py` is deleted and CI workflows
point to `python -m mapvalidator` instead.

## Non-Goals

- Replacing the existing XSD schema validation (it stays as a first pass)
- Testing tile rendering quality or visual correctness
- Supporting map formats beyond MOBAC XML
- Building a web dashboard for monitoring

## Architecture

### Package Layout

```text
mapvalidator/                # Python package
  __init__.py
  xml_checks.py              # Deterministic XML validation
  probe.py                   # HTTP liveness with dual user-agent
  reporter.py                # Console output + GitHub issue management
  __main__.py                # CLI entry point

tests/
  conftest.py                # Shared fixtures from real XML files
  test_xml_checks.py
  test_probe.py              # Uses `responses` library for HTTP mocking
  test_reporter.py

.github/workflows/
  validate-maps-deep.yml     # PR validation (no probing)
  map-health-check.yml       # Weekly cron with probing + issue management
  test-mapvalidator.yml      # pytest on .py changes

pyproject.toml               # uv-managed, pytest config, coverage thresholds

scripts/
  validate.sh                # Validate all XML files (no network)
  probe.sh                   # Validate + probe all tile servers
  test-map.sh                # Validate + probe a single XML file
```

### Module Responsibilities

#### `xml_checks.py` — Pure Deterministic Validation

All checks derived from ATAK's `MobacMapSourceFactory.java` parser behavior.

**Checks performed:**
| Check | Severity | Rationale |
|-------|----------|-----------|
| minZoom > maxZoom | ERROR | Inverted range, map won't load |
| maxZoom > 25 | ERROR | Well beyond any tile server ceiling |
| maxZoom > 22 | WARN | Uncommon but some servers (e.g. Canadian WMS) legitimately serve 23 |
| minZoom < 0 | ERROR | Invalid zoom level |
| TMS URL missing {$x}/{$y}/{$z} or {$q} | ERROR | No tiles can be fetched |
| Empty URL | ERROR | Non-functional map |
| WMS missing layers | ERROR | WMS requires layer specification |
| WMS missing tileType | ERROR | Required by parser (`tileFormat` maps to image MIME type) |
| Duplicate map name across corpus | ERROR | Confusing in ATAK map selector |
| Filename contains spaces | ERROR | Shell scripts and CI break |
| Filename non-ASCII | ERROR | Cross-platform compatibility |
| URL has `{$serverpart}` but no `<serverParts>` element (or vice versa) | ERROR | URL substitution will produce broken tile requests |
| coordinateSystem camelCase | WARN | ATAK parser only reads `<coordinatesystem>` (lowercase); camelCase silently ignored |
| HTTP instead of HTTPS | WARN | Security, some servers redirect |
| serverParts comma-separated | WARN | ATAK splits on `\s+` (whitespace); commas treated as part of hostname |
| tileType not in {PNG, JPG, JPEG} | WARN | Only known-good values; others may indicate a typo |
| WMS missing version | WARN | Version determines CRS vs SRS parameter (1.3.x→CRS, others→SRS); wrong default may break projection |
| `invertYCoordinate` not exactly `"true"` or `"false"` | WARN | Parser uses `equals("true")` (case-sensitive); `"True"` silently fails |
| Missing tileType (TMS only) | INFO | TMS stores as-is; informational |
| `backgroundColor` with >1 hex digit | INFO | ATAK parser regular expression `#[0-9A-Fa-f]` only matches single-digit values (parser bug) |
| SRIDs 900913 or 90094326 used | INFO | Auto-converted to EPSG:3857/4326 at runtime |
| `tileUpdate` non-numeric value (e.g. `None`, `IfNoneMatch`) | WARN | ATAK parser uses `\d+` regular expression; non-numeric values silently ignored — element has no effect |
| WMS `<aditionalparameters>` (single-d typo) used | INFO | ATAK accepts both spellings but the typo form may confuse contributors |
| WMS `<version>` has leading/trailing whitespace | WARN | ATAK uses `equals("1.3")` (exact match); `" 1.3.0 "` won't match, breaking CRS/SRS selection |

**Interface:**
```python
@dataclass
class ValidationResult:
    filepath: Path
    map_name: str
    source_type: str  # TMS, WMS, Multi-Layer
    errors: list[str]
    warnings: list[str]
    info: list[str]

def validate_file(filepath: Path) -> ValidationResult: ...
def validate_corpus(directory: Path) -> list[ValidationResult]: ...
def check_duplicates(results: list[ValidationResult]) -> list[str]: ...
```

#### `probe.py` — Dual User-Agent Liveness

Probes each map source with two user-agents to distinguish "server dead" from "ATAK blocked."

**Classification matrix:**
| TAK UA | Generic UA | Status | Action |
|--------|-----------|--------|--------|
| 200 + image | 200 + image (similar size) | HEALTHY | None |
| 200 + image | 200 + image (size diverges >2x) | BLOCKED | Issue: "Soft block — different content per UA" |
| 403/429 | 200 + image | BLOCKED | Issue: "Map X blocks ATAK clients" |
| fail | fail | DEAD | Issue: "Map X server unreachable" |
| 200 + non-image | 200 + image | DEGRADED | Issue: "Map X returns error page to ATAK" |

**Probe behavior:**
- Tries multiple zoom levels per source: `[minZoom, 3, 0]` (first success wins)
- For TMS: substitutes z/x/y or quadkey into URL template
- For WMS: constructs GetMap request with `service=WMS&request=GetMap`, source's `layers`, `version` (default 1.1.1), `SRS=EPSG:4326` (or `CRS=CRS:84` for 1.3.x), `format=image/png`, `width=256&height=256`, and a global bbox `-180,-90,180,90` (EPSG:4326) to guarantee a valid response regardless of layer extent
- Validates response is actually an image (Content-Type check)
- Soft-block detection: compares response content sizes between user-agents; if both return images but sizes differ by more than 2x, classifies as BLOCKED (catches servers like OpenStreetMap that serve a "403 Access blocked" PNG image with HTTP 200 to the TAK user-agent)
- Timeout: 10s per request
- Rate limiting: 0.5s delay between requests
- User agents: `TAK` (matches ATAK hardcoded header) and `Mozilla/5.0 (compatible)`

**Interface:**
```python
class ProbeStatus(Enum):
    HEALTHY = "healthy"
    BLOCKED = "blocked"
    DEAD = "dead"
    DEGRADED = "degraded"

@dataclass
class ProbeResult:
    filepath: Path
    map_name: str
    status: ProbeStatus
    tak_status_code: int | None
    tak_error: str | None
    generic_status_code: int | None
    generic_error: str | None
    test_url: str

def probe_source(root: ET.Element, filepath: Path) -> ProbeResult: ...
def probe_all(directory: Path) -> list[ProbeResult]: ...
```

#### `reporter.py` — Output & GitHub Issue Management

**Console output** (for local runs and CI logs):
- Summary table with status per map
- Grouped by status (errors first, then warnings)
- Exit code 1 if any errors

**GitHub issue management** (for cron jobs):
- Creates issues labeled `map-health` for new failures
- Issue title format: `Map Health: {map_name} — {DEAD|BLOCKED|DEGRADED}`
- Issue body includes: probe details, test URLs tried, suggested action
- Deduplication: searches open issues by title prefix before creating
- Auto-close: if a previously-failing source now passes, closes the issue with a comment
- Uses `gh` CLI (subprocess) — no GitHub API library dependency

**Interface:**
```python
def print_report(
    validations: list[ValidationResult],
    probes: list[ProbeResult] | None = None,
) -> None: ...

def manage_github_issues(
    probes: list[ProbeResult],
    repo: str = "joshuafuller/ATAK-Maps",
) -> None: ...
```

#### `__main__.py` — CLI Entry Point

```bash
python -m mapvalidator                    # XML checks only (fast)
python -m mapvalidator --probe            # XML checks + liveness probing
python -m mapvalidator --probe --issues   # + create/close GitHub issues
python -m mapvalidator --smoke            # Quick probe of 3 reliable + OSM control
```

### Test Strategy

Tests are structured by what they're testing, not by abstraction layer.

#### Unit Tests: `test_xml_checks.py`

**Fixtures:** Real XML files from the repository, loaded via `conftest.py`. Additional synthetic XML strings for edge cases.

**Tests include:**
- Every XML file in corpus parses without error
- Every XML file has required fields for its type
- Every TMS URL contains valid placeholders
- Zoom range: corpus property test (all files satisfy minZoom <= maxZoom <= 25)
- Known bad cases: craft XML with inverted zoom, missing placeholders, spaces in filename, camelCase coordinateSystem, comma serverParts, HTTP URL, duplicate names
- Each check function tested independently with minimal input
- Coverage target: 95%+ on `xml_checks.py`

#### Contract Tests: `test_probe.py`

**HTTP Mocking:** Uses the `responses` library to mock `requests` at the transport level — no recorded cassette files on disk. Mock responses are defined inline in test functions (`probe.py` uses the `requests` library for HTTP).

**Tests include:**
- 200 + `image/png` Content-Type → HEALTHY
- 200 + `text/html` Content-Type → DEGRADED (error page, not a tile)
- 403 → correctly classified per UA combination
- 404, 500 → correctly classified
- DNS failure (ConnectionError) → DEAD
- Timeout → DEAD
- **OSM control case:** TAK UA gets 403, generic UA gets 200 → BLOCKED. This is a hardcoded assertion — if it ever returns HEALTHY, the test fails because our probe logic is wrong.
- Multi-zoom fallback: first zoom 404, second zoom 200 → HEALTHY
- serverParts substitution: space-delimited correctly picks first part
- WMS URL construction: verify GetMap params are well-formed
- Coverage target: 90%+ on `probe.py`

#### Integration Tests: `test_reporter.py`

**Approach:** Mock `subprocess.run` for `gh` CLI calls.

**Tests include:**
- Console report formatting with mixed errors/warnings/healthy
- GitHub issue creation: verify `gh issue create` command and payload
- Dedup: mock existing open issue → no new issue created
- Auto-close: mock resolved source → `gh issue close` called
- Empty results: no issues created
- Coverage target: 80%+ on `reporter.py`

### CI/CD Workflows

#### `validate-maps-deep.yml` — PR Validation

```yaml
on:
  pull_request:
    paths: ["**/*.xml", "mapvalidator/**", "tests/**"]
  push:
    branches: [master]
    paths: ["**/*.xml"]
```

- Installs uv, runs `uv sync`
- Runs `python -m mapvalidator` (XML checks only, no probing)
- Fast, deterministic, no network calls
- Fails PR on errors

#### `map-health-check.yml` — Weekly Monitoring

```yaml
on:
  schedule:
    - cron: "0 0 * * 0"  # Sunday midnight UTC
  workflow_dispatch:
```

- Runs `python -m mapvalidator --probe --issues`
- Creates/closes GitHub issues labeled `map-health`
- Also runnable manually via workflow_dispatch

#### `test-mapvalidator.yml` — Test Suite

```yaml
on:
  pull_request:
    paths: ["mapvalidator/**", "tests/**", "pyproject.toml"]
  push:
    branches: [master]
    paths: ["mapvalidator/**", "tests/**"]
```

- Installs uv, runs `uv sync --dev`
- Runs `pytest --cov=mapvalidator --cov-fail-under=80`
- No network calls (HTTP mocked via `responses` library)

### Python Environment

**Managed with `uv`:**

```toml
# pyproject.toml
[project]
name = "atak-maps-validator"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["requests"]

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "responses"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=mapvalidator --cov-report=term-missing"

[tool.coverage.run]
source = ["mapvalidator"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

**Local workflow:**
```bash
uv sync --dev          # Install deps
uv run pytest          # Run tests
uv run python -m mapvalidator --probe  # Run validation locally
```

### Release ZIP Exclusion

The release workflow (`map-release.yml`) uses `git ls-files -z '*.xml'` — only XML files are included. The `mapvalidator/`, `tests/`, `pyproject.toml`, etc. are all non-XML and won't leak into the release ZIP.

The catalog generator (`generate-catalog.py`) excludes `{".github", ".git", "schema", "dist", "docs"}`. The existing `validate-maps-deep.py` has a separate set that also includes `"images"`. Will unify both by adding `mapvalidator`, `tests`, and `images` to `generate-catalog.py`'s `EXCLUDE_DIRS`.

## ATAK Source Reference

Parser behavior derived from `atak-civ-client` source:
- `takkernel/.../mobac/MobacMapSourceFactory.java` — XML parsing, element handling
- `takkernel/.../mobac/MobacTileClient2.java` — HTTP requests, `TAK` user-agent
- `takkernel/.../mobac/CustomMobacMapSource.java` — TMS URL template substitution, connection config
- `takkernel/.../mobac/CustomWmsMobacMapSource.java` — WMS GetMap construction, CRS/SRS version logic

Key parser facts codified as validation rules:
- `coordinatesystem` must be lowercase (camelCase silently ignored)
- `serverParts` is split on `\s+` (whitespace-delimited, not comma)
- `tileUpdate` only accepts digits (`\d+` pattern; string values like "None" silently default to 0)
- `backgroundColor` pattern `#[0-9A-Fa-f]` only matches single hex digit (parser bug — `#FFFFFF` never parses)
- `invertYCoordinate` requires exact string `"true"` (case-sensitive; `"True"` is false)
- User-Agent is hardcoded `TAK`; also sends `x-common-site-name: {map name}`
- Timeouts: with config object, both connect and read use `config.connectTimeout` (likely ATAK bug — same value for both); without config, fallback is connect=3000ms, read=5000ms
- URLs and `additionalParameters` are HTML-entity-unescaped (`&amp;` → `&`) — validator must not flag escaped entities in URLs as malformed
- WMS version determines projection parameter: 1.3.x uses `CRS` param with `CRS:84`, others use `SRS` param with `EPSG:` prefix
- WMS default SRID is 4326 (WGS84); TMS default SRID is 3857 (Web Mercator)
- `maxZoom` is required (defaults to -1, parse fails if absent)
- SRIDs 900913 and 90094326 are auto-converted to proper EPSG codes at runtime

## Implementation Order

1. `pyproject.toml` + `mapvalidator/__init__.py` — skeleton
2. `xml_checks.py` + `test_xml_checks.py` — TDD red/green/refactor (refactor logic from existing `validate-maps-deep.py`)
3. `probe.py` + `test_probe.py` — TDD with `responses` library for HTTP mocking (refactor probe logic from existing script; switch from `urllib` to `requests`)
4. `reporter.py` + `test_reporter.py` — TDD with mocked subprocess
5. `__main__.py` — wire it all together
6. Delete `.github/scripts/validate-maps-deep.py` — all logic now lives in `mapvalidator/`
7. CI workflows — `validate-maps-deep.yml`, `test-mapvalidator.yml`, `map-health-check.yml`
8. Update `generate-catalog.py` `EXCLUDE_DIRS` — add `mapvalidator`, `tests`, `images`
9. Fix known issues — Finland dead DNS, HTTP→HTTPS, serverParts, casing, openseamap coordinateSystem
10. Verify OSM control case — confirm TAK UA block behavior is correctly mocked in `test_probe.py`
