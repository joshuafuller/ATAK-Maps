# Map Validation & Liveness Monitoring — Design Spec

**Date:** 2026-03-13
**Branch:** `feature/map-liveness-checks`
**Audience:** Maintainer + contributors (fast PR feedback + ongoing monitoring)

## Problem

The ATAK-Maps repo has 36 XML map source files with no validation beyond basic XSD schema checks. The schema only validates structure — it can't catch:

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
3. TDD test suite with 80%+ coverage, using real XML fixtures and HTTP cassettes
4. Automated weekly monitoring with GitHub issue creation for failures
5. Fast PR feedback for contributors on XML quality

## Non-Goals

- Replacing the existing XSD schema validation (it stays as a first pass)
- Testing tile rendering quality or visual correctness
- Supporting map formats beyond MOBAC XML
- Building a web dashboard for monitoring

## Architecture

### Package Layout

```
mapvalidator/                # Python package
  __init__.py
  xml_checks.py              # Deterministic XML validation
  probe.py                   # HTTP liveness with dual user-agent
  reporter.py                # Console output + GitHub issue management
  __main__.py                # CLI entry point

tests/
  conftest.py                # Shared fixtures from real XML files
  cassettes/                 # Recorded HTTP responses
    tile_200_png.bin
    tile_200_html_error.bin
    blocked_403.bin
    not_found_404.bin
    server_error_500.bin
    dns_failure.bin
    timeout.bin
    osm_tak_blocked.bin      # Control case: OSM blocks TAK UA
    osm_generic_ok.bin       # Control case: OSM allows generic UA
  test_xml_checks.py
  test_probe.py
  test_reporter.py

.github/workflows/
  validate-maps-deep.yml     # PR validation (no probing)
  map-health-check.yml       # Weekly cron with probing + issue management
  test-mapvalidator.yml      # pytest on .py changes

pyproject.toml               # uv-managed, pytest config, coverage thresholds
```

### Module Responsibilities

#### `xml_checks.py` — Pure Deterministic Validation

All checks derived from ATAK's `MobacMapSourceFactory.java` parser behavior.

**Checks performed:**
| Check | Severity | Rationale |
|-------|----------|-----------|
| minZoom > maxZoom | ERROR | Inverted range, map won't load |
| maxZoom > 22 | ERROR | No tile servers serve beyond 22 |
| minZoom < 0 | ERROR | Invalid zoom level |
| TMS URL missing {$x}/{$y}/{$z} or {$q} | ERROR | No tiles can be fetched |
| Empty URL | ERROR | Non-functional map |
| WMS missing layers | ERROR | WMS requires layer specification |
| Duplicate map name across corpus | ERROR | Confusing in ATAK map selector |
| Filename contains spaces | ERROR | Shell scripts and CI break |
| Filename non-ASCII | ERROR | Cross-platform compatibility |
| coordinateSystem camelCase | WARN | ATAK parser silently ignores it |
| HTTP instead of HTTPS | WARN | Security, some servers redirect |
| serverParts comma-separated | WARN | ATAK expects space-separated |
| tileType unknown value | WARN | May indicate a typo |
| WMS missing version | WARN | Defaults may not match server |
| Missing tileType | INFO | Informational for TMS |

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
| 200 + image | 200 + image | HEALTHY | None |
| 403/429 | 200 + image | BLOCKED | Issue: "Map X blocks ATAK clients" |
| fail | fail | DEAD | Issue: "Map X server unreachable" |
| 200 + non-image | 200 + image | DEGRADED | Issue: "Map X returns error page to ATAK" |

**Probe behavior:**
- Tries multiple zoom levels per source: `[minZoom, 3, 0]` (first success wins)
- For TMS: substitutes z/x/y or quadkey into URL template
- For WMS: constructs minimal GetMap request
- Validates response is actually an image (Content-Type check)
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

```
python -m mapvalidator                    # XML checks only (fast)
python -m mapvalidator --probe            # XML checks + liveness probing
python -m mapvalidator --probe --issues   # + create/close GitHub issues
python -m mapvalidator --smoke            # Quick probe of 3 reliable + OSM control
```

### Test Strategy

Tests are structured by what they're testing, not by abstraction layer.

#### Unit Tests: `test_xml_checks.py`

**Fixtures:** Real XML files from the repo, loaded via `conftest.py`. Additional synthetic XML strings for edge cases.

**Tests include:**
- Every XML file in corpus parses without error
- Every XML file has required fields for its type
- Every TMS URL contains valid placeholders
- Zoom range: corpus property test (all files satisfy minZoom <= maxZoom <= 22)
- Known bad cases: craft XML with inverted zoom, missing placeholders, spaces in filename, camelCase coordinateSystem, comma serverParts, HTTP URL, duplicate names
- Each check function tested independently with minimal input
- Coverage target: 95%+ on `xml_checks.py`

#### Contract Tests: `test_probe.py`

**Cassettes:** Pre-recorded HTTP responses stored as files in `tests/cassettes/`. Using the `responses` library to mock `urllib` at the transport level.

**Tests include:**
- 200 + image/png Content-Type → HEALTHY
- 200 + text/html Content-Type → DEGRADED (error page, not a tile)
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
- No network calls (cassettes only)

### Python Environment

**Managed with `uv`:**

```toml
# pyproject.toml
[project]
name = "atak-maps-validator"
version = "0.1.0"
requires-python = ">=3.10"

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

The catalog generator (`generate-catalog.py`) already excludes non-map directories. Will add `mapvalidator` and `tests` to its `EXCLUDE_DIRS` set.

## ATAK Source Reference

Parser behavior derived from `atak-civ-client` source:
- `takkernel/.../mobac/MobacMapSourceFactory.java` — XML parsing, element handling
- `takkernel/.../mobac/MobacTileClient2.java` — HTTP requests, `TAK` user-agent
- `takkernel/.../mobac/AbstractMobacMapSource.java` — URL template substitution

Key parser facts codified as validation rules:
- `coordinatesystem` must be lowercase (camelCase silently ignored)
- `serverParts` is space-delimited
- `tileUpdate` only accepts integers (string values like "None" are ignored)
- `backgroundColor` regex is broken in parser (never actually parses)
- User-Agent is hardcoded `TAK`
- Connect timeout 3000ms, read timeout 5000ms

## Implementation Order

1. `pyproject.toml` + `mapvalidator/__init__.py` — skeleton
2. `xml_checks.py` + `test_xml_checks.py` — TDD red/green/refactor
3. `probe.py` + `test_probe.py` + cassettes — TDD with recorded responses
4. `reporter.py` + `test_reporter.py` — TDD with mocked subprocess
5. `__main__.py` — wire it all together
6. CI workflows — `validate-maps-deep.yml`, `test-mapvalidator.yml`, `map-health-check.yml`
7. Fix known issues — Canada zoom, Finland dead DNS, HTTP→HTTPS, serverParts, casing
8. Record OSM cassette — live capture of TAK UA block for control case
