"""XML validation checks for ATAK map source files.

Performs structural and semantic checks that XSD schema validation cannot
express, such as zoom level sanity, URL placeholder presence, duplicate
map names, and filename conventions.
"""

from dataclasses import dataclass, field
from pathlib import Path
import os
import re
import xml.etree.ElementTree as ET

EXCLUDE_DIRS = {".github", ".git", "schema", "dist", "docs", "images", "mapvalidator", "tests"}
VALID_TILE_TYPES = {"png", "jpg", "jpeg"}

# Zoom thresholds
_MAX_ZOOM_HARD = 25   # above this is ERROR
_MAX_ZOOM_SOFT = 22   # above this but <= hard is WARN


@dataclass
class ValidationResult:
    filepath: Path
    map_name: str
    source_type: str  # "TMS", "WMS", "Multi-Layer"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)


def _source_type_from_tag(tag: str) -> str:
    """Map XML root tag to human-readable source type."""
    mapping = {
        "customMapSource": "TMS",
        "customWmsMapSource": "WMS",
        "customMultiLayerMapSource": "Multi-Layer",
    }
    return mapping.get(tag, "TMS")


def _check_filename(filepath: Path, result: ValidationResult) -> None:
    """Check filename for spaces and non-ASCII characters."""
    name = filepath.name
    if " " in name:
        result.errors.append(f"Filename contains spaces: {name}")
    if not name.isascii():
        result.errors.append(f"Filename contains non-ASCII characters: {name}")


def _check_zoom_levels(root: ET.Element, result: ValidationResult) -> None:
    """Validate zoom level sanity."""
    min_zoom_text = root.findtext("minZoom")
    max_zoom_text = root.findtext("maxZoom")

    if max_zoom_text is None:
        result.errors.append("Missing required <maxZoom>")
        return

    try:
        max_zoom = int(max_zoom_text)
    except ValueError:
        result.errors.append(f"<maxZoom> is not a valid integer: {max_zoom_text}")
        return

    if max_zoom > _MAX_ZOOM_HARD:
        result.errors.append(
            f"<maxZoom> is {max_zoom}, exceeds maximum of {_MAX_ZOOM_HARD}"
        )
    elif max_zoom > _MAX_ZOOM_SOFT:
        result.warnings.append(
            f"<maxZoom> is {max_zoom}, exceeds typical maximum of {_MAX_ZOOM_SOFT}"
        )

    if min_zoom_text is not None:
        try:
            min_zoom = int(min_zoom_text)
        except ValueError:
            result.errors.append(
                f"<minZoom> is not a valid integer: {min_zoom_text}"
            )
            return

        if min_zoom < 0:
            result.errors.append(f"<minZoom> is < 0: {min_zoom}")
        if min_zoom > max_zoom:
            result.errors.append(
                f"<minZoom> ({min_zoom}) > <maxZoom> ({max_zoom})"
            )


def _check_tms_url(root: ET.Element, result: ValidationResult) -> None:
    """Validate TMS URL has required placeholders."""
    url = root.findtext("url") or ""
    if not url.strip():
        result.errors.append("Empty <url> element")
        return

    has_xyz = all(p in url for p in ["{$x}", "{$y}", "{$z}"])
    has_quadkey = "{$q}" in url
    if not has_xyz and not has_quadkey:
        result.errors.append(
            f"TMS URL missing placeholders (need {{$x}}/{{$y}}/{{$z}} or {{$q}}): "
            f"{url[:80]}"
        )


def _check_wms_source(root: ET.Element, result: ValidationResult) -> None:
    """Validate WMS-specific requirements."""
    url = root.findtext("url") or ""
    if not url.strip():
        result.errors.append("Empty <url> element")

    layers = root.findtext("layers")
    if not layers or not layers.strip():
        result.errors.append("WMS source missing <layers> element")

    tile_type = root.findtext("tileType")
    if not tile_type or not tile_type.strip():
        result.errors.append("WMS source missing <tileType> element")

    version = root.findtext("version")
    if not version or not version.strip():
        result.warnings.append(
            "WMS source missing <version> element (recommended: 1.3.0)"
        )


def _check_tile_type(root: ET.Element, result: ValidationResult) -> None:
    """Validate tileType is a known value; for TMS, missing is INFO."""
    tile_type = root.findtext("tileType")
    source_type = _source_type_from_tag(root.tag)

    if tile_type is None or not tile_type.strip():
        if source_type == "TMS":
            result.info.append("Missing <tileType> element (informational)")
        return

    if tile_type.strip().lower() not in VALID_TILE_TYPES:
        result.warnings.append(
            f"Unknown <tileType>: {tile_type} (expected: png, jpg, jpeg)"
        )


def _check_serverparts(root: ET.Element, result: ValidationResult) -> None:
    """Check consistency between {$serverpart} in URL and <serverParts> element."""
    url = root.findtext("url") or ""
    server_parts_el = root.find("serverParts")
    has_placeholder = "{$serverpart}" in url

    if server_parts_el is not None:
        sp_text = (server_parts_el.text or "").strip()
        has_element = bool(sp_text)
    else:
        has_element = False

    if has_placeholder and not has_element:
        result.errors.append(
            "URL contains {$serverpart} but no <serverParts> element with values"
        )
    elif has_element and not has_placeholder:
        result.errors.append(
            "<serverParts> element present but URL does not use {$serverpart}"
        )

    # Comma warning
    if has_element:
        sp_text = (server_parts_el.text or "").strip()
        if "," in sp_text:
            result.warnings.append(
                "serverParts uses commas — ATAK splits on whitespace; "
                "commas become part of hostname"
            )


def _check_coordinate_system(root: ET.Element, result: ValidationResult) -> None:
    """Check coordinateSystem camelCase and known SRID values."""
    # camelCase check: element named coordinateSystem instead of coordinatesystem
    cs_camel = root.find("coordinateSystem")
    if cs_camel is not None:
        result.warnings.append(
            "Element <coordinateSystem> uses camelCase — ATAK only reads "
            "<coordinatesystem> (all lowercase)"
        )

    # SRID info checks on the lowercase variant
    cs = root.findtext("coordinatesystem") or ""
    if cs_camel is not None and not cs:
        cs = cs_camel.text or ""

    if "900913" in cs:
        result.info.append(
            f"coordinatesystem contains SRID 900913 — auto-converted at runtime"
        )
    if "90094326" in cs:
        result.info.append(
            f"coordinatesystem contains SRID 90094326 — auto-converted at runtime"
        )


def _check_http_url(root: ET.Element, result: ValidationResult) -> None:
    """Warn if URL uses HTTP instead of HTTPS."""
    url = root.findtext("url") or ""
    if url.strip().lower().startswith("http://"):
        result.warnings.append(
            f"URL uses HTTP instead of HTTPS — consider upgrading for security"
        )


def _check_invert_y(root: ET.Element, result: ValidationResult) -> None:
    """Warn if invertYCoordinate is not exactly 'true' or 'false'."""
    el = root.findtext("invertYCoordinate")
    if el is not None and el.strip() not in ("true", "false"):
        result.warnings.append(
            f"<invertYCoordinate> is '{el.strip()}' — parser is case-sensitive, "
            f"must be exactly 'true' or 'false'"
        )


def _check_tile_update(root: ET.Element, result: ValidationResult) -> None:
    """Warn if tileUpdate is present but non-numeric (ATAK regex \\d+ silently ignores)."""
    tu = root.findtext("tileUpdate")
    if tu is not None:
        tu = tu.strip()
        if tu and not re.fullmatch(r"\d+", tu):
            result.warnings.append(
                f"<tileUpdate> is '{tu}' — ATAK only accepts numeric values "
                f"(digits only); non-numeric values are silently ignored"
            )


def _check_additional_parameters(root: ET.Element, result: ValidationResult) -> None:
    """Info if WMS source uses misspelled 'aditionalparameters' element."""
    if root.tag != "customWmsMapSource":
        return
    typo_el = root.find("aditionalparameters")
    correct_el = root.find("additionalparameters")
    if typo_el is not None and correct_el is None:
        result.info.append(
            "<aditionalparameters> uses the misspelled form (single 'd') — "
            "ATAK accepts both spellings, but consider using "
            "<additionalparameters> for clarity"
        )


def _check_version_whitespace(root: ET.Element, result: ValidationResult) -> None:
    """Warn if WMS version has leading/trailing whitespace."""
    if root.tag != "customWmsMapSource":
        return
    version = root.findtext("version")
    if version is not None and version != version.strip():
        result.warnings.append(
            f"<version> has leading/trailing whitespace: '{version}' — "
            f"ATAK uses exact string comparison (equals()), "
            f"whitespace will prevent version-specific behavior (CRS vs SRS)"
        )


def _check_background_color(root: ET.Element, result: ValidationResult) -> None:
    """Info if backgroundColor has >1 hex digit after #."""
    bg = root.findtext("backgroundColor") or ""
    bg = bg.strip()
    if bg.startswith("#") and len(bg) > 2:
        result.info.append(
            f"<backgroundColor> '{bg}' has >1 hex digit after # — "
            f"ATAK parser bug only matches single digit"
        )


def validate_file(filepath: Path) -> ValidationResult:
    """Run all checks on a single XML map file and return a ValidationResult."""
    result = ValidationResult(
        filepath=filepath,
        map_name="",
        source_type="TMS",
    )

    # Filename checks
    _check_filename(filepath, result)

    # Parse XML
    try:
        tree = ET.parse(filepath)
    except ET.ParseError as e:
        result.errors.append(f"XML parse error: {e}")
        return result

    root = tree.getroot()
    result.map_name = root.findtext("name") or "Unknown"
    result.source_type = _source_type_from_tag(root.tag)

    # Zoom level checks
    _check_zoom_levels(root, result)

    # Tile type checks
    _check_tile_type(root, result)

    # Type-specific checks
    if root.tag == "customMapSource":
        _check_tms_url(root, result)
    elif root.tag == "customWmsMapSource":
        _check_wms_source(root, result)

    # Common checks
    _check_serverparts(root, result)
    _check_coordinate_system(root, result)
    _check_http_url(root, result)
    _check_invert_y(root, result)
    _check_tile_update(root, result)
    _check_background_color(root, result)
    _check_additional_parameters(root, result)
    _check_version_whitespace(root, result)

    return result


def validate_corpus(directory: Path) -> list[ValidationResult]:
    """Validate all XML map files under `directory`, skipping excluded dirs."""
    results = []
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in sorted(filenames):
            if fname.lower().endswith(".xml"):
                filepath = Path(dirpath) / fname
                results.append(validate_file(filepath))
    return sorted(results, key=lambda r: r.filepath)


def check_duplicates(results: list[ValidationResult]) -> list[str]:
    """Check for duplicate map names across a set of ValidationResults.

    Returns a list of error strings for each duplicate found.
    """
    seen: dict[str, Path] = {}
    errors: list[str] = []
    for r in results:
        name = r.map_name
        if not name or name == "Unknown":
            continue
        if name in seen:
            errors.append(
                f"Duplicate map name '{name}': {seen[name]} and {r.filepath}"
            )
        else:
            seen[name] = r.filepath
    return errors
