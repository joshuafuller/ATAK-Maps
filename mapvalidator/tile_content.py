"""Decide whether a tile response is real map data.

Servers often answer HTTP 200 with something that is not a map tile: an
OGC/HTML error page, a solid-colour or fully transparent tile outside their
data, or a branded placeholder ("Map data not yet available", "Access
blocked"). ATAK caches all of these as if they were real tiles.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

# sha256 of known placeholder tiles (see tests/fixtures/tiles).
KNOWN_PLACEHOLDERS = {
    "9eafd300d61393184a4abc1d458564cfd1cd9b6f9c4e9c74687045c0a0e5b858": "Esri 'Map data not yet available'",
    "b02c44252dac5a5e820ecef1e9bf9200e9407c042df668a466a1aa81a9ecca7a": "OpenStreetMap 'Access blocked'",
    "45d35034a62d30443e492851752f67f439b95a908fce54de601f7373fcb7ab05": "Bing 'no imagery'",
}


@dataclass
class TileVerdict:
    # image | placeholder | blank (one opaque colour) | empty (fully transparent) | error
    kind: str
    transparent_fraction: float = 0.0
    detail: str = ""


def classify_tile(body: bytes, content_type: str | None) -> TileVerdict:
    if not body:
        return TileVerdict("error", detail="empty response body")
    placeholder = KNOWN_PLACEHOLDERS.get(hashlib.sha256(body).hexdigest())
    if placeholder:
        return TileVerdict("placeholder", detail=placeholder)
    try:
        img = Image.open(io.BytesIO(body))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError):
        snippet = body[:80].decode("utf-8", "replace").strip()
        return TileVerdict("error", detail=f"not an image ({content_type}): {snippet}")

    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A").histogram()
    total = sum(alpha)
    transparent = alpha[0] / total
    if transparent == 1.0:
        return TileVerdict("empty", transparent_fraction=1.0)
    if transparent == 0.0 and rgba.getcolors(maxcolors=1) is not None:
        return TileVerdict("blank", detail="single opaque colour")
    return TileVerdict("image", transparent_fraction=transparent)
