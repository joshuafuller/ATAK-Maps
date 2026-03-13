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

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROBE_TIMEOUT = 10
PROBE_DELAY = 0.5
TAK_USER_AGENT = "TAK"
GENERIC_USER_AGENT = "Mozilla/5.0 (compatible)"

EXCLUDE_DIRS_DEFAULT = {".github", ".git", "schema", "dist", "docs", "images"}

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

def build_test_urls(root: ET.Element) -> list[str]:
    """Build test tile URLs for liveness probing from an XML root element.

    Returns a list of URLs to try (first success wins).
    """
    tag = root.tag
    url = root.findtext("url", "")
    if not url.strip():
        return []

    min_zoom = int(root.findtext("minZoom", "0"))

    if tag == "customMapSource":
        test_zooms = sorted(set([min_zoom, 3, 0]))
        urls = []
        for z in test_zooms:
            test_url = (
                url.replace("{$z}", str(z))
                .replace("{$x}", "0")
                .replace("{$y}", "0")
            )
            # Quadkey: zoom 0 -> "0" (max(z,1) digits of "0")
            test_url = test_url.replace("{$q}", "0" * max(z, 1))
            # Server parts: space-delimited, pick first one
            server_parts = root.findtext("serverParts", "")
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
) -> tuple[int | None, str | None, bool]:
    """Probe a single URL and return (status_code, error_message, is_image).

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
        if status == 200:
            content_type = resp.headers.get("Content-Type", "")
            is_image = (
                content_type.startswith("image/")
                or content_type.startswith("application/octet-stream")
            )
            return (200, None, is_image)
        else:
            return (status, f"HTTP {status}", False)
    except requests.exceptions.ConnectionError as e:
        return (None, f"Connection failed: {e}", False)
    except requests.exceptions.Timeout as e:
        return (None, f"Timeout: {e}", False)
    except Exception as e:
        return (None, f"Error: {e}", False)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(
    tak_result: tuple[int | None, str | None, bool],
    generic_result: tuple[int | None, str | None, bool],
) -> ProbeStatus:
    """Classify probe results into a ProbeStatus.

    | TAK UA         | Generic UA     | Status   |
    |----------------|----------------|----------|
    | 200 + image    | 200 + image    | HEALTHY  |
    | 403/429        | 200 + image    | BLOCKED  |
    | fail           | fail           | DEAD     |
    | 200 + non-image| 200 + image    | DEGRADED |
    """
    tak_code, tak_err, tak_is_image = tak_result
    gen_code, gen_err, gen_is_image = generic_result

    gen_ok = gen_code == 200 and gen_is_image
    tak_ok = tak_code == 200 and tak_is_image

    if tak_ok and gen_ok:
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
    best_tak = (None, "No URLs probed", False)
    best_generic = (None, "No URLs probed", False)
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
        if root.tag not in ("customMapSource", "customWmsMapSource", "customMultiLayerMapSource"):
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
        if root.tag not in ("customMapSource", "customWmsMapSource", "customMultiLayerMapSource"):
            continue

        result = probe_source(root, filepath)
        results.append(result)

        if len(results) > 1:
            time.sleep(PROBE_DELAY)

    return results
