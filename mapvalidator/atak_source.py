"""Parse map XML and build tile URLs exactly the way ATAK does.

Ported from the ATAK CIV 5.5 takkernel sources:
- MobacMapSourceFactory (XML parsing, defaults)
- CustomMobacMapSource.getUrl / getQuadKey / loadTile (TMS URLs, invertY)
- CustomWmsMobacMapSource.getUrl / fixupURL (WMS GetMap URLs)
- OSMWebMercator / WebMercatorProjection / EquirectangularMapProjection
"""

from __future__ import annotations

import html
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

_EARTH_A = 6378137.0  # WebMercatorProjection.a
_OSM_MAX_LAT = math.degrees(
    math.atan(math.sinh(math.pi))
)  # OSMUtils.mapnikTileLat(0, 0)
_WMS_FORMATS = {"JPG": "image/jpeg", "PNG": "image/png"}  # CustomWmsMobacMapSource


@dataclass
class AtakSource:
    kind: str  # "tms", "wms" or "multi"
    name: str | None
    min_zoom: int = 0
    max_zoom: int = -1
    tile_type: str | None = None
    url: str | None = None
    server_parts: list[str] | None = None
    invert_y: bool = False
    srid: int = 3857
    layers: str | None = None
    style: str | None = None
    version: str | None = None
    additional_parameters: str | None = None
    children: list[AtakSource] = field(default_factory=list)


def _text(el: ET.Element, tag: str) -> str | None:
    child = el.find(tag)
    return child.text if child is not None else None


def _srid(el: ET.Element, default: int) -> int:
    cs = _text(el, "coordinatesystem")
    if cs and re.fullmatch(r"EPSG:\d+", cs):
        return int(cs.split(":")[1])
    return default


def _url(el: ET.Element) -> str | None:
    # XmlPullParser.getText() already decoded entities; ATAK then calls
    # Strings.unescapeHtml on top, so entities are decoded twice.
    raw = _text(el, "url")
    return html.unescape(raw) if raw is not None else None


def _int(el: ET.Element, tag: str, default: int) -> int:
    value = _text(el, tag)
    return int(value) if value is not None else default


def _parse_tms(el: ET.Element) -> AtakSource:
    parts = _text(el, "serverParts")
    return AtakSource(
        kind="tms",
        name=_text(el, "name"),
        min_zoom=_int(el, "minZoom", 0),
        max_zoom=_int(el, "maxZoom", -1),
        tile_type=_text(el, "tileType"),
        url=_url(el),
        server_parts=parts.split() if parts and parts.strip() else None,
        invert_y=_text(el, "invertYCoordinate") == "true",
        srid=_srid(el, 3857),
    )


def _parse_wms(el: ET.Element) -> AtakSource:
    tile_type = _text(el, "tileType")
    additional = _text(el, "additionalparameters")
    if additional is None:
        additional = _text(el, "aditionalparameters")
    return AtakSource(
        kind="wms",
        name=_text(el, "name"),
        min_zoom=_int(el, "minZoom", 0),
        max_zoom=_int(el, "maxZoom", -1),
        tile_type=tile_type.upper() if tile_type is not None else None,
        url=_url(el),
        srid=_srid(el, 4326),
        layers=_text(el, "layers"),
        style=_text(el, "styles"),
        version=_text(el, "version"),
        additional_parameters=additional,
    )


def _parse(el: ET.Element) -> AtakSource:
    if el.tag == "customMapSource":
        return _parse_tms(el)
    if el.tag == "customWmsMapSource":
        return _parse_wms(el)
    if el.tag == "customMultiLayerMapSource":
        layers = el.find("layers")
        children = [_parse(c) for c in (list(layers) if layers is not None else [])]
        return AtakSource(
            kind="multi",
            name=_text(el, "name"),
            min_zoom=min((c.min_zoom for c in children), default=0),
            max_zoom=max((c.max_zoom for c in children), default=-1),
            children=children,
        )
    raise ValueError(f"unsupported root element <{el.tag}>")


def parse_source(path: Path) -> AtakSource:
    return _parse(ET.parse(path).getroot())


def java_double(value: float) -> str:
    """Format a double like Java's String.valueOf(double)."""
    if value == 0.0:
        return "-0.0" if math.copysign(1.0, value) < 0 else "0.0"
    sign, digits, exp = Decimal(repr(value)).normalize().as_tuple()
    exponent = int(exp)  # finite doubles only; 'n'/'N'/'F' are NaN/inf
    digits_str = "".join(map(str, digits))
    point = len(digits_str) + exponent  # position of the decimal point
    prefix = "-" if sign else ""
    if 1e-3 <= abs(value) < 1e7:
        if point <= 0:
            return f"{prefix}0.{'0' * -point}{digits_str}"
        if point >= len(digits_str):
            return f"{prefix}{digits_str}{'0' * (point - len(digits_str))}.0"
        return f"{prefix}{digits_str[:point]}.{digits_str[point:]}"
    mantissa = digits_str[0] + "." + (digits_str[1:] or "0")
    return f"{prefix}{mantissa}E{point - 1}"


def _quadkey(zoom: int, x: int, y: int) -> str:
    out = []
    for i in range(zoom, 0, -1):
        mask = 1 << (i - 1)
        digit = (1 if x & mask else 0) + (2 if y & mask else 0)
        out.append(str(digit))
    return "".join(out)


def _forward(srid: int, lat: float, lon: float) -> tuple[float, float]:
    if srid in (3857, 900913):
        return (
            _EARTH_A * math.radians(lon),
            _EARTH_A * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)),
        )
    return lon, lat


def _bounds(srid: int) -> tuple[float, float, float, float]:
    """(north, west, south, east) of the projection, as in the WMS source."""
    if srid in (3857, 900913):
        return _OSM_MAX_LAT, -180.0, -_OSM_MAX_LAT, 180.0
    return 90.0, -180.0, -90.0, 180.0


def _grid_width(srid: int) -> int:
    return 2 if srid == 4326 else 1


def _fixup_wms_url(url: str) -> str:
    query = urlsplit(url).query
    if "?" not in url:
        return url + "?"
    if query and not query.endswith("&"):
        return url + "&"
    return url


def _wms_url(src: AtakSource, zoom: int, x: int, y: int) -> str:
    north, west, south, east = _bounds(src.srid)
    ul_x, ul_y = _forward(src.srid, north, west)
    lr_x, lr_y = _forward(src.srid, south, east)
    dx = (lr_x - ul_x) / _grid_width(src.srid)
    dy = (ul_y - lr_y) / 1
    tile_s = ul_y - ((dy / (1 << zoom)) * (y + 1))
    tile_w = ul_x + ((dx / (1 << zoom)) * x)
    tile_n = ul_y - ((dy / (1 << zoom)) * y)
    tile_e = ul_x + ((dx / (1 << zoom)) * (x + 1))

    v13 = src.version in ("1.3.1", "1.3.0")
    crs = "CRS:84" if v13 and src.srid == 4326 else f"EPSG:{src.srid}"
    fmt = _WMS_FORMATS.get(src.tile_type or "")
    out = _fixup_wms_url(src.url or "")
    out += f"service=WMS&request=GetMap&layers={src.layers}&{'crs' if v13 else 'srs'}={crs}"
    out += f"&format={fmt if fmt is not None else 'null'}&width=256&height=256"
    out += f"&version={src.version if src.version is not None else '1.1.1'}"
    out += f"&styles={src.style if src.style is not None else ''}"
    if src.additional_parameters is not None:
        out += src.additional_parameters
    out += "&bbox=" + ",".join(java_double(v) for v in (tile_w, tile_s, tile_e, tile_n))
    return out


def tile_url(src: AtakSource, zoom: int, x: int, y: int, server_part: int = 0) -> str:
    """The URL ATAK requests for tile (zoom, x, y)."""
    if src.kind == "wms":
        return _wms_url(src, zoom, x, y)
    if src.kind != "tms":
        raise ValueError("multi-layer sources have one URL per child")
    if src.invert_y:
        y = ((1 << zoom) - 1) - y
    out = src.url or ""
    if src.server_parts:
        out = out.replace(
            "{$serverpart}", src.server_parts[server_part % len(src.server_parts)]
        )
    out = out.replace("{$x}", str(x)).replace("{$y}", str(y)).replace("{$z}", str(zoom))
    return out.replace("{$q}", _quadkey(zoom, x, y))


def tile_for_point(
    src: AtakSource, lat: float, lon: float, zoom: int
) -> tuple[int, int]:
    """The (x, y) of the tile that contains a point, in the source's tile grid."""
    if src.srid == 4326:
        size = 180.0 / (1 << zoom)
        return int((lon + 180.0) // size), int((90.0 - lat) // size)
    n = 1 << zoom
    lat_r = math.radians(lat)
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n)
    return x, y
