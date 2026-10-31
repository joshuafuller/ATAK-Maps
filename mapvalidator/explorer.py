"""Data for the site's map explorer (docs/maps/): every map as a live web layer.

The explorer draws maps with Leaflet in the browser, so each map's tile URL is
converted with the same rules ATAK uses (see atak_source). Each entry also
carries a region, a source credit and a place where the map has data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import parse_qsl

from mapvalidator.atak_source import AtakSource, parse_source
from mapvalidator.catalog import RAW_BASE, build_map_entry, is_overlay, iter_map_files
from mapvalidator.harness import DEFAULT_TEST_POINT

# First match wins; checked against the map's description text.
REGIONS = [
    ("United States", "US"),
    ("BLM", "US"),
    ("Great Britain", "UK"),
    ("German", "DE"),
    ("Canad", "CA"),
    ("British Columbia", "CA"),
    ("Poland", "PL"),
    ("Polish", "PL"),
    ("Europe", "Europe"),
]

OSM = "© OpenStreetMap contributors"
# Source credit shown on the live map: by folder, overlays by file-name prefix.
CREDITS = {
    "google": "© Google",
    "bing": "© Microsoft Bing",
    "esri": "© Esri and its data providers",
    "usgs": "USGS The National Map",
    "naip": "USDA NAIP",
    "blm": "Bureau of Land Management",
    "ca-nrcan": "© Natural Resources Canada",
    "de-basemap": "© BKG basemap.de",
    "pl-geoportal": "© GUGiK Geoportal",
    "uk-os": "© Ordnance Survey",
    "opentopo": f"© OpenTopoMap (CC-BY-SA), {OSM}",
    "cyclosm": f"© CyclOSM, {OSM}",
    "mtbmap": f"© MTBMap.cz, {OSM}",
    "openseamap": f"© OpenSeaMap, {OSM}",
}
OVERLAY_CREDITS = {
    "grg_google": "© Google",
    "grg_fema": "FEMA National Flood Hazard Layer",
    "grg_blm": "Bureau of Land Management",
    "grg_ca_bc": "© Province of British Columbia (DataBC)",
    "grg_openseamap": f"© OpenSeaMap, {OSM}",
    "grg_waymarked": f"© Waymarked Trails, {OSM}",
}

BLOB_BASE = "https://github.com/joshuafuller/ATAK-Maps/blob/master"

LivePoint = Callable[[], Optional[tuple]]


def leaf_specs(src: AtakSource) -> list[dict]:
    """Leaflet layer specs for a source; a multi-layer source flattens to its layers."""
    if src.kind == "multi":
        return [spec for child in src.children for spec in leaf_specs(child)]
    spec: dict = {"min": src.min_zoom, "max": src.max_zoom}
    if src.kind == "wms":
        base, _, query = (src.url or "").partition("?")
        extra = dict(parse_qsl((query + (src.additional_parameters or "")).lstrip("&")))
        spec.update(
            kind="wms",
            base=base,
            layers=src.layers or "",
            version=src.version or "1.1.1",
            format=(
                "image/png" if (src.tile_type or "").upper() == "PNG" else "image/jpeg"
            ),
            extra=extra,
        )
        return [spec]
    url = (
        (src.url or "")
        .replace("{$z}", "{z}")
        .replace("{$x}", "{x}")
        .replace("{$y}", "{y}")
    )
    url = url.replace("{$serverpart}", "{s}").replace("{$q}", "{q}")
    spec.update(
        kind="tms",
        url=url,
        subdomains=src.server_parts or [],
        tms=src.invert_y,
        quadkey="{q}" in url,
    )
    return [spec]


def region_for(text: str) -> str:
    return next((code for key, code in REGIONS if key in text), "Global")


def credit_for(rel: Path) -> str:
    if is_overlay(rel):
        return next(
            (v for k, v in OVERLAY_CREDITS.items() if rel.stem.startswith(k)), ""
        )
    return CREDITS.get(rel.parent.name, "")


def build_explorer_data(
    root: Path, descriptions: dict, live_points: Optional[dict[str, LivePoint]] = None
) -> list[dict]:
    """One entry per map: name, type, region, test point, import link and layers."""
    out = []
    for f in iter_map_files(root):
        entry = build_map_entry(f, root)
        src = parse_source(f)
        d = descriptions.get(entry["slug"]) or {}
        text = d.get("text", "")
        point, zoom = list(d.get("test_point") or DEFAULT_TEST_POINT), None
        live = (live_points or {}).get(entry["slug"])
        found = live() if live else None
        if found:
            point, zoom = found
        out.append(
            {
                "slug": entry["slug"],
                "name": entry["name"],
                "category": d.get("category", "Other"),
                "text": text,
                "region": region_for(text),
                "point": point,
                "zoom": zoom,
                "overlay": is_overlay(f),
                "needsKey": entry["needs_key"],
                "importUri": entry["import_uri"],
                "xmlUrl": entry["import_url"],  # site copy, served as application/xml
                "sourceUrl": entry["raw_url"].replace(RAW_BASE, BLOB_BASE),
                "credit": credit_for(f.relative_to(root)),
                "min": src.min_zoom,
                "max": src.max_zoom,
                "layers": leaf_specs(src),
            }
        )
    return out


def health_js(path: Path) -> str:
    """map-health.json (from the harness --json) as a script for the page; {} if absent."""
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        data = {}
    return "window.ATAK_HEALTH = " + json.dumps(data) + ";\n"


BC_FIRES_WFS = (
    "https://openmaps.gov.bc.ca/geo/pub/wfs?service=WFS&version=2.0.0&request=GetFeature"
    "&typeNames=pub:WHSE_LAND_AND_NATURAL_RESOURCE.PROT_CURRENT_FIRE_POLYS_SP&count=1"
    "&sortBy=FIRE_SIZE_HECTARES+D&outputFormat=application/json&srsName=EPSG:4326"
)


def largest_bc_fire() -> Optional[tuple]:
    """Centre of this season's largest BC fire perimeter, so the overlay opens on real data.

    Fire perimeters change every season, so a fixed test point goes empty.
    Returns None when the service cannot be reached.
    """
    import requests

    try:
        feat = requests.get(BC_FIRES_WFS, timeout=30).json()["features"][0]
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None

    def points(c):
        if isinstance(c[0], (int, float)):
            yield c
        else:
            for x in c:
                yield from points(x)

    xy = list(points(feat["geometry"]["coordinates"]))
    lons, lats = [p[0] for p in xy], [p[1] for p in xy]
    return [
        round((min(lats) + max(lats)) / 2, 4),
        round((min(lons) + max(lons)) / 2, 4),
    ], 10


LIVE_POINTS: dict[str, LivePoint] = {"grg-grg-ca-bc-wildfire": largest_bc_fire}
