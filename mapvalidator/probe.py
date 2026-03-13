"""Tile server liveness probing for ATAK map sources.

Builds test URLs from MOBAC XML map source definitions and probes them
with dual user-agents (TAK and generic browser) to classify server health.
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import urllib3

import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROBE_TIMEOUT = 10
PROBE_DELAY = 0.5
TAK_USER_AGENT = "TAK"
GENERIC_USER_AGENT = "Mozilla/5.0 (compatible)"

EXCLUDE_DIRS_DEFAULT = {
    ".github",
    ".git",
    "schema",
    "dist",
    "docs",
    "images",
    "mapvalidator",
    "tests",
}

SMOKE_SOURCES = [
    "Google/google_hybrid.xml",
    "ESRI/esri_clarity.xml",
    "Bing/Bing_Satellite.xml",
]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# URL construction
# ---------------------------------------------------------------------------


def _tile_to_quadkey(z: int, x: int, y: int) -> str:
    """Convert tile coordinates to a Bing Maps quadkey string."""
    if z <= 0:
        return "0"
    result = []
    for i in range(z, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if x & mask:
            digit += 1
        if y & mask:
            digit += 2
        result.append(str(digit))
    return "".join(result)


def build_test_urls(root: ET.Element) -> list[str]:
    """Build test tile URLs for liveness probing from an XML root element.

    Returns a list of URLs to try (first success wins).
    """
    tag = root.tag
    url = root.findtext("url", "")
    if not url.strip():
        return []

    try:
        min_zoom = int(root.findtext("minZoom", "0"))
    except ValueError:
        min_zoom = 0

    if tag == "customMapSource":
        # Test coordinates at different zoom levels.  (0,0) is ocean, so we
        # also probe tiles covering populated land (Western Europe / Eastern US)
        # to avoid false-positive DEAD on regionally-scoped servers.
        test_tiles: list[tuple[int, int, int]] = [
            (min_zoom, 0, 0),
            (3, 4, 2),  # Western Europe at zoom 3
            (3, 2, 3),  # Eastern US at zoom 3
            (0, 0, 0),
            (8, 134, 86),  # Central Europe at zoom 8
        ]
        # Deduplicate while preserving order
        seen: set[tuple[int, int, int]] = set()
        unique_tiles: list[tuple[int, int, int]] = []
        for tile in test_tiles:
            if tile not in seen:
                seen.add(tile)
                unique_tiles.append(tile)

        urls = []
        server_parts = root.findtext("serverParts", "")
        for z, x, y in unique_tiles:
            test_url = (
                url.replace("{$z}", str(z))
                .replace("{$x}", str(x))
                .replace("{$y}", str(y))
            )
            # Quadkey for the given tile coordinates
            test_url = test_url.replace("{$q}", _tile_to_quadkey(z, x, y))
            if "{$serverpart}" in test_url and server_parts:
                first_part = server_parts.split()[0]
                test_url = test_url.replace("{$serverpart}", first_part)
            urls.append(test_url)
        return urls

    elif tag == "customWmsMapSource":
        base = url.strip().rstrip("?").rstrip("&")
        sep = "?" if "?" not in base else "&"
        layers = root.findtext("layers", "")
        tile_type = root.findtext("tileType", "PNG")
        version = root.findtext("version", "1.3.0")
        # ATAK source: version 1.3.x uses CRS param with CRS:84 for EPSG:4326
        use_crs = version.startswith("1.3")
        crs_param = "CRS" if use_crs else "SRS"
        coord_sys = root.findtext("coordinatesystem", "EPSG:4326")
        if use_crs and coord_sys == "EPSG:4326":
            coord_sys = "CRS:84"

        fmt = f"image/{tile_type.lower()}"
        if tile_type.lower() == "jpg":
            fmt = "image/jpeg"

        params = (
            f"{sep}SERVICE=WMS&REQUEST=GetMap&VERSION={version}"
            f"&{crs_param}={coord_sys}&LAYERS={layers}"
            f"&BBOX=-180,-90,180,90&WIDTH=256&HEIGHT=256&FORMAT={fmt}"
            f"&STYLES="
        )
        return [base + params]

    return []


# ---------------------------------------------------------------------------
# HTTP probing
# ---------------------------------------------------------------------------


def probe_url(
    url: str, user_agent: str, timeout: int = PROBE_TIMEOUT
) -> tuple[int | None, str | None, bool, int]:
    """Probe a single URL and return (status_code, error_message, is_image, content_length).

    Uses requests library with SSL verification disabled.
    """
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": user_agent},
            timeout=timeout,
            verify=False,
        )
        status = resp.status_code
        content_length = len(resp.content)
        if status == 200:
            content_type = resp.headers.get("Content-Type", "")
            is_image = content_type.startswith("image/") or content_type.startswith(
                "application/octet-stream"
            )
            return (200, None, is_image, content_length)
        else:
            return (status, f"HTTP {status}", False, 0)
    except requests.exceptions.ConnectionError as e:
        return (None, f"Connection failed: {e}", False, 0)
    except requests.exceptions.Timeout as e:
        return (None, f"Timeout: {e}", False, 0)
    except Exception as e:
        return (None, f"Error: {e}", False, 0)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classify(
    tak_result: tuple[int | None, str | None, bool, int],
    generic_result: tuple[int | None, str | None, bool, int],
) -> ProbeStatus:
    """Classify probe results into a ProbeStatus.

    | TAK UA         | Generic UA     | Status   |
    |----------------|----------------|----------|
    | 200 + image    | 200 + image    | HEALTHY  |
    | 200 + image*   | 200 + image    | BLOCKED  | *content size diverges >2x
    | 403/429        | 200 + image    | BLOCKED  |
    | fail           | fail           | DEAD     |
    | 200 + non-image| 200 + image    | DEGRADED |
    """
    tak_code, tak_err, tak_is_image, tak_size = tak_result
    gen_code, gen_err, gen_is_image, gen_size = generic_result

    gen_ok = gen_code == 200 and gen_is_image
    tak_ok = tak_code == 200 and tak_is_image

    if tak_ok and gen_ok:
        # Soft-block detection: if both return images but the content sizes
        # differ by more than 2x, the server is likely serving a block-notice
        # image to TAK (e.g. OSM returns a "403 Access blocked" PNG with
        # HTTP 200 to the TAK user-agent).
        larger = max(tak_size, gen_size)
        smaller = min(tak_size, gen_size)
        if smaller > 0 and larger > 2 * smaller:
            return ProbeStatus.BLOCKED
        return ProbeStatus.HEALTHY

    if tak_code in (403, 429) and gen_ok:
        return ProbeStatus.BLOCKED

    if tak_code == 200 and not tak_is_image and gen_ok:
        return ProbeStatus.DEGRADED

    return ProbeStatus.DEAD


# ---------------------------------------------------------------------------
# Source-level probing
# ---------------------------------------------------------------------------


def probe_source(root: ET.Element, filepath: Path) -> ProbeResult:
    """Probe a single map source with both user agents.

    Tries multiple zoom-level URLs; first successful probe wins.
    """
    map_name = root.findtext("name", "Unknown")
    test_urls = build_test_urls(root)

    if not test_urls:
        return ProbeResult(
            filepath=filepath,
            map_name=map_name,
            status=ProbeStatus.DEAD,
            tak_status_code=None,
            tak_error="No test URLs could be built",
            generic_status_code=None,
            generic_error="No test URLs could be built",
            test_url="",
        )

    # Try each URL; first one where at least one UA gets a 200 wins
    best_tak: tuple[int | None, str | None, bool, int] = (
        None,
        "No URLs probed",
        False,
        0,
    )
    best_generic: tuple[int | None, str | None, bool, int] = (
        None,
        "No URLs probed",
        False,
        0,
    )
    best_url = test_urls[0]

    for url in test_urls:
        tak_result = probe_url(url, TAK_USER_AGENT)
        generic_result = probe_url(url, GENERIC_USER_AGENT)

        tak_code = tak_result[0]
        gen_code = generic_result[0]

        # If either got a 200, use this URL's results
        if tak_code == 200 or gen_code == 200:
            best_tak = tak_result
            best_generic = generic_result
            best_url = url
            break

        # Keep last results as fallback
        best_tak = tak_result
        best_generic = generic_result
        best_url = url

    status = classify(best_tak, best_generic)

    return ProbeResult(
        filepath=filepath,
        map_name=map_name,
        status=status,
        tak_status_code=best_tak[0],
        tak_error=best_tak[1],
        generic_status_code=best_generic[0],
        generic_error=best_generic[1],
        test_url=best_url,
    )


# ---------------------------------------------------------------------------
# Directory-level probing
# ---------------------------------------------------------------------------


def probe_smoke(directory: Path) -> list[ProbeResult]:
    """Probe only the SMOKE_SOURCES for a fast sanity check.

    Skips sources whose files don't exist in the directory.
    """
    results: list[ProbeResult] = []

    for rel_path in SMOKE_SOURCES:
        filepath = directory / rel_path
        if not filepath.is_file():
            continue

        try:
            tree = ET.parse(filepath)
        except ET.ParseError:
            continue

        root = tree.getroot()
        if root.tag not in (
            "customMapSource",
            "customWmsMapSource",
            "customMultiLayerMapSource",
        ):
            continue

        result = probe_source(root, filepath)
        results.append(result)

        if len(results) > 1:
            time.sleep(PROBE_DELAY)

    return results


def probe_all(
    directory: Path,
    exclude_dirs: set[str] | None = None,
    smoke_only: bool = False,
) -> list[ProbeResult]:
    """Probe XML map sources in a directory tree.

    If smoke_only is True, probes only the SMOKE_SOURCES subset.
    Otherwise walks the full directory and probes every XML file.
    Rate-limits requests with PROBE_DELAY between sources.
    """
    if smoke_only:
        return probe_smoke(directory)

    if exclude_dirs is None:
        exclude_dirs = EXCLUDE_DIRS_DEFAULT

    results: list[ProbeResult] = []
    xml_files = sorted(directory.rglob("*.xml"))

    for filepath in xml_files:
        # Skip excluded directories
        if any(part in exclude_dirs for part in filepath.relative_to(directory).parts):
            continue

        try:
            tree = ET.parse(filepath)
        except ET.ParseError:
            continue

        root = tree.getroot()
        if root.tag not in (
            "customMapSource",
            "customWmsMapSource",
            "customMultiLayerMapSource",
        ):
            continue

        result = probe_source(root, filepath)
        results.append(result)

        if len(results) > 1:
            time.sleep(PROBE_DELAY)

    return results
