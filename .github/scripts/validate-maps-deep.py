#!/usr/bin/env python3
"""Deep validation of ATAK map XML files.

Checks that XSD schema cannot express:
  - Zoom level sanity (minZoom < maxZoom, maxZoom <= 22)
  - URL placeholder presence ({$x},{$y},{$z} or {$q} for TMS)
  - tileType is a known value
  - No duplicate map names
  - Filename conventions (no spaces, ASCII only)
  - WMS sources have version element
  - Tile server liveness (optional, --probe flag)
"""

import argparse
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXCLUDE_DIRS = {".github", ".git", "schema", "dist", "docs", "images"}
VALID_TILE_TYPES = {"png", "jpg", "jpeg", "PNG", "JPG", "JPEG"}
MAX_ZOOM_CEILING = 22
PROBE_TIMEOUT = 10
PROBE_DELAY = 0.5  # seconds between requests


def find_xml_files():
    xml_files = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            if fname.lower().endswith(".xml"):
                xml_files.append(Path(dirpath) / fname)
    return sorted(xml_files)


def check_filename(filepath):
    """Check filename conventions."""
    issues = []
    name = filepath.name
    if " " in name:
        issues.append(f"Filename contains spaces: {name}")
    if not name.isascii():
        issues.append(f"Filename contains non-ASCII characters: {name}")
    return issues


def check_zoom_levels(root, filepath):
    """Validate zoom level sanity."""
    issues = []
    min_zoom_el = root.findtext("minZoom")
    max_zoom_el = root.findtext("maxZoom")

    if max_zoom_el is None:
        issues.append("Missing required <maxZoom>")
        return issues

    try:
        max_zoom = int(max_zoom_el)
    except ValueError:
        issues.append(f"<maxZoom> is not a valid integer: {max_zoom_el}")
        return issues

    if max_zoom > MAX_ZOOM_CEILING:
        issues.append(f"<maxZoom> is {max_zoom}, exceeds maximum of {MAX_ZOOM_CEILING}")

    if min_zoom_el is not None:
        try:
            min_zoom = int(min_zoom_el)
            if min_zoom > max_zoom:
                issues.append(f"<minZoom> ({min_zoom}) > <maxZoom> ({max_zoom})")
            if min_zoom < 0:
                issues.append(f"<minZoom> is negative: {min_zoom}")
        except ValueError:
            issues.append(f"<minZoom> is not a valid integer: {min_zoom_el}")

    return issues


def check_tms_url(root):
    """Validate TMS URL has required placeholders."""
    issues = []
    url = root.findtext("url", "")
    if not url.strip():
        issues.append("Empty <url> element")
        return issues

    has_xyz = all(p in url for p in ["{$x}", "{$y}", "{$z}"])
    has_quadkey = "{$q}" in url
    if not has_xyz and not has_quadkey:
        issues.append(f"TMS URL missing placeholders (need {{$x}}/{{$y}}/{{$z}} or {{$q}}): {url[:80]}")

    return issues


def check_wms_source(root):
    """Validate WMS-specific requirements."""
    issues = []
    url = root.findtext("url", "")
    if not url.strip():
        issues.append("Empty <url> element")

    layers = root.findtext("layers")
    if not layers or not layers.strip():
        issues.append("WMS source missing <layers> element")

    version = root.findtext("version")
    if not version:
        issues.append("WMS source missing <version> element (recommended: 1.3.0)")

    return issues


def check_tile_type(root):
    """Validate tileType is a known value."""
    issues = []
    tile_type = root.findtext("tileType")
    if tile_type and tile_type not in VALID_TILE_TYPES:
        issues.append(f"Unknown <tileType>: {tile_type} (expected: {', '.join(sorted(VALID_TILE_TYPES))})")
    return issues


def build_test_urls(root):
    """Build test tile URLs for liveness probing. Returns list of URLs to try."""
    tag = root.tag
    url = root.findtext("url", "")
    if not url.strip():
        return []

    min_zoom = int(root.findtext("minZoom", "0"))

    if tag == "customMapSource":
        # Try minZoom first, then zoom 3 as fallback (populated but lightweight)
        test_zooms = sorted(set([min_zoom, 3, 0]))
        urls = []
        for z in test_zooms:
            test_url = url.replace("{$z}", str(z)).replace("{$x}", "0").replace("{$y}", "0")
            # Quadkey: zoom 0 = "0", zoom 1 = "0", etc.
            test_url = test_url.replace("{$q}", "0" * max(z, 1))
            # Server parts: space-delimited in MOBAC format, pick first one
            server_parts = root.findtext("serverParts", "")
            if "{$serverpart}" in test_url and server_parts:
                first_part = server_parts.split()[0]
                test_url = test_url.replace("{$serverpart}", first_part)
            urls.append(test_url)
        return urls

    elif tag == "customWmsMapSource":
        # WMS: build a GetMap request for a world-extent tile
        base = url.strip().rstrip("?").rstrip("&")
        sep = "?" if "?" not in base else "&"
        layers = root.findtext("layers", "")
        tile_type = root.findtext("tileType", "PNG")
        version = root.findtext("version", "1.3.0")
        crs_param = "CRS" if version >= "1.3.0" else "SRS"
        coord_sys = root.findtext("coordinatesystem", "EPSG:4326")

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


def probe_url(test_url, timeout=PROBE_TIMEOUT):
    """Probe a tile URL and return (status_code, error_msg)."""
    import urllib.request
    import urllib.error
    import ssl

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        test_url,
        headers={"User-Agent": "TAK"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        content_type = resp.headers.get("Content-Type", "")
        status = resp.status
        resp.close()
        if status == 200:
            if "image" in content_type or "octet" in content_type:
                return status, None
            else:
                return status, f"Got 200 but Content-Type is {content_type} (expected image)"
        return status, f"HTTP {status}"
    except urllib.error.HTTPError as e:
        return e.code, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, f"Connection failed: {e.reason}"
    except Exception as e:
        return None, f"Error: {e}"


def validate_file(filepath, do_probe=False):
    """Run all checks on a single XML file."""
    rel_path = filepath.relative_to(REPO_ROOT)
    errors = []
    warnings = []

    # Filename checks
    errors.extend(check_filename(filepath))

    # Parse XML
    try:
        tree = ET.parse(filepath)
    except ET.ParseError as e:
        errors.append(f"XML parse error: {e}")
        return rel_path, errors, warnings, None

    root = tree.getroot()
    tag = root.tag
    name = root.findtext("name", "Unknown")

    # Zoom level checks
    errors.extend(check_zoom_levels(root, filepath))

    # Tile type checks
    warnings.extend(check_tile_type(root))

    # Type-specific checks
    if tag == "customMapSource":
        errors.extend(check_tms_url(root))
    elif tag == "customWmsMapSource":
        wms_issues = check_wms_source(root)
        # Missing version is a warning, not error
        for issue in wms_issues:
            if "version" in issue.lower():
                warnings.append(issue)
            else:
                errors.append(issue)
    elif tag == "customMultiLayerMapSource":
        pass  # Composite layers validated by their children

    # Liveness probe — try multiple zoom levels, pass on first success
    probe_result = None
    if do_probe and tag in ("customMapSource", "customWmsMapSource"):
        test_urls = build_test_urls(root)
        last_err = None
        for test_url in test_urls:
            status, err = probe_url(test_url)
            if not err:
                probe_result = ("OK", None)
                break
            last_err = f"{err} — {test_url[:100]}"
        else:
            if last_err:
                probe_result = ("FAIL", last_err)

    return rel_path, errors, warnings, probe_result


def main():
    parser = argparse.ArgumentParser(description="Deep validation of ATAK map XML files")
    parser.add_argument("--probe", action="store_true", help="Test tile server liveness")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("files", nargs="*", help="Specific files to check (default: all)")
    args = parser.parse_args()

    if args.files:
        xml_files = [Path(f).resolve() for f in args.files]
    else:
        xml_files = find_xml_files()

    print(f"Validating {len(xml_files)} XML map files...")
    if args.probe:
        print(f"Liveness probing enabled (timeout: {PROBE_TIMEOUT}s per source)\n")
    print()

    all_names = {}  # name -> filepath for duplicate detection
    total_errors = 0
    total_warnings = 0
    probe_ok = 0
    probe_fail = 0

    for filepath in xml_files:
        rel_path, errors, warnings, probe_result = validate_file(filepath, do_probe=args.probe)

        # Duplicate name check
        try:
            tree = ET.parse(filepath)
            name = tree.getroot().findtext("name", "")
            if name:
                if name in all_names:
                    errors.append(f"Duplicate map name '{name}' (also in {all_names[name]})")
                else:
                    all_names[name] = rel_path
        except ET.ParseError:
            pass

        # Output
        has_issues = errors or warnings or (probe_result and probe_result[0] == "FAIL")
        if has_issues:
            print(f"{'FAIL' if errors else 'WARN'} {rel_path}")
            for e in errors:
                print(f"  ERROR: {e}")
                total_errors += 1
            for w in warnings:
                print(f"  WARN:  {w}")
                total_warnings += 1
            if probe_result and probe_result[0] == "FAIL":
                print(f"  PROBE: {probe_result[1]}")
                probe_fail += 1
        else:
            status = ""
            if probe_result:
                status = " [tile OK]"
                probe_ok += 1
            print(f"  OK {rel_path}{status}")

        if args.probe:
            time.sleep(PROBE_DELAY)

    # Summary
    print(f"\n{'='*60}")
    print(f"Files checked: {len(xml_files)}")
    print(f"Errors: {total_errors}")
    print(f"Warnings: {total_warnings}")
    if args.probe:
        print(f"Tile probes: {probe_ok} OK, {probe_fail} failed")

    if total_errors > 0 or (args.strict and total_warnings > 0):
        print("\nValidation FAILED")
        sys.exit(1)
    else:
        print("\nValidation PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
