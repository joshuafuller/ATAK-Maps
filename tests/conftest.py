"""Shared fixtures for ATAK Maps validation tests."""

import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def repo_root():
    """Return the repository root path."""
    return REPO_ROOT


@pytest.fixture
def real_xml_files(repo_root):
    """Collect all real XML map files from the repo (excluding non-map dirs)."""
    from mapvalidator.xml_checks import EXCLUDE_DIRS

    xml_files = []
    for dirpath in repo_root.rglob("*.xml"):
        # dirpath is the file path from rglob
        parts = dirpath.relative_to(repo_root).parts
        if not any(p in EXCLUDE_DIRS for p in parts):
            xml_files.append(dirpath)
    return sorted(xml_files)


@pytest.fixture
def tmp_xml(tmp_path):
    """Factory fixture: write XML content to a temp file and return its Path."""
    def _make(xml_content: str, filename: str = "test_map.xml") -> Path:
        filepath = tmp_path / filename
        filepath.write_text(textwrap.dedent(xml_content).strip(), encoding="utf-8")
        return filepath
    return _make


# --- Synthetic XML strings for edge-case tests ---

VALID_TMS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Test TMS Map</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

VALID_WMS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customWmsMapSource>
    <name>Test WMS Map</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <version>1.3.0</version>
    <layers>test_layer</layers>
    <url>https://wms.example.com/wms?</url>
    <coordinatesystem>EPSG:3857</coordinatesystem>
</customWmsMapSource>
"""

INVERTED_ZOOM_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Inverted Zoom</name>
    <minZoom>10</minZoom>
    <maxZoom>5</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

MAX_ZOOM_26_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Max Zoom 26</name>
    <minZoom>0</minZoom>
    <maxZoom>26</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

MAX_ZOOM_23_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Max Zoom 23</name>
    <minZoom>0</minZoom>
    <maxZoom>23</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

MISSING_URL_PLACEHOLDERS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>No Placeholders</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/some/path</url>
</customMapSource>
"""

EMPTY_URL_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Empty URL</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url></url>
</customMapSource>
"""

WMS_MISSING_LAYERS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customWmsMapSource>
    <name>WMS No Layers</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <version>1.3.0</version>
    <url>https://wms.example.com/wms?</url>
    <coordinatesystem>EPSG:3857</coordinatesystem>
</customWmsMapSource>
"""

WMS_MISSING_TILETYPE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customWmsMapSource>
    <name>WMS No TileType</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <version>1.3.0</version>
    <layers>test_layer</layers>
    <url>https://wms.example.com/wms?</url>
    <coordinatesystem>EPSG:3857</coordinatesystem>
</customWmsMapSource>
"""

CAMELCASE_COORDSYS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>CamelCase CoordSys</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
    <coordinateSystem>EPSG:3857</coordinateSystem>
</customMapSource>
"""

COMMA_SERVERPARTS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Comma ServerParts</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://{$serverpart}.example.com/{$z}/{$x}/{$y}.png</url>
    <serverParts>a,b,c</serverParts>
</customMapSource>
"""

HTTP_URL_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>HTTP Map</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>http://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

UNKNOWN_TILETYPE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>GIF TileType</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>gif</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.gif</url>
</customMapSource>
"""

WMS_MISSING_VERSION_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customWmsMapSource>
    <name>WMS No Version</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <layers>test_layer</layers>
    <url>https://wms.example.com/wms?</url>
    <coordinatesystem>EPSG:3857</coordinatesystem>
</customWmsMapSource>
"""

INVERT_Y_CAPITAL_TRUE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>InvertY Capital</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
    <invertYCoordinate>True</invertYCoordinate>
</customMapSource>
"""

SERVERPART_URL_NO_ELEMENT_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>ServerPart URL No Element</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://{$serverpart}.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

SERVERPARTS_ELEMENT_NO_URL_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>ServerParts Element No URL</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
    <serverParts>a b c</serverParts>
</customMapSource>
"""

BGCOLOR_MULTI_HEX_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>BgColor Multi Hex</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
    <backgroundColor>#FFFFFF</backgroundColor>
</customMapSource>
"""

COORDSYS_900913_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>CoordSys 900913</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
    <coordinatesystem>EPSG:900913</coordinatesystem>
</customMapSource>
"""

QUADKEY_TMS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Quadkey Map</name>
    <minZoom>0</minZoom>
    <maxZoom>20</maxZoom>
    <tileType>jpg</tileType>
    <url>https://ecn.t2.tiles.virtualearth.net/tiles/a{$q}?g=761</url>
</customMapSource>
"""

NEGATIVE_MINZOOM_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Negative MinZoom</name>
    <minZoom>-1</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

MISSING_TILETYPE_TMS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>No TileType TMS</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

TILE_UPDATE_NONE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>TileUpdate None</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <tileUpdate>None</tileUpdate>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

TILE_UPDATE_IFNONEMATCH_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>TileUpdate IfNoneMatch</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <tileUpdate>IfNoneMatch</tileUpdate>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

TILE_UPDATE_NUMERIC_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>TileUpdate Numeric</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <tileUpdate>604800000</tileUpdate>
    <url>https://tiles.example.com/{$z}/{$x}/{$y}.png</url>
</customMapSource>
"""

WMS_ADITIONALPARAMETERS_TYPO_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customWmsMapSource>
    <name>WMS Typo Params</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <version>1.3.0</version>
    <layers>test_layer</layers>
    <url>https://wms.example.com/wms?</url>
    <coordinatesystem>EPSG:3857</coordinatesystem>
    <aditionalparameters>TRANSPARENT=TRUE</aditionalparameters>
</customWmsMapSource>
"""

WMS_ADDITIONALPARAMETERS_CORRECT_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customWmsMapSource>
    <name>WMS Correct Params</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <version>1.3.0</version>
    <layers>test_layer</layers>
    <url>https://wms.example.com/wms?</url>
    <coordinatesystem>EPSG:3857</coordinatesystem>
    <additionalparameters>TRANSPARENT=TRUE</additionalparameters>
</customWmsMapSource>
"""

VERSION_WHITESPACE_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customWmsMapSource>
    <name>WMS Version Whitespace</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <version> 1.3.0 </version>
    <layers>test_layer</layers>
    <url>https://wms.example.com/wms?</url>
    <coordinatesystem>EPSG:3857</coordinatesystem>
</customWmsMapSource>
"""

EMPTY_SERVERPARTS_NO_PLACEHOLDER_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Empty ServerParts</name>
    <minZoom>0</minZoom>
    <maxZoom>20</maxZoom>
    <tileType>jpg</tileType>
    <url>https://ecn.t2.tiles.virtualearth.net/tiles/a{$q}?g=761</url>
    <serverParts></serverParts>
</customMapSource>
"""
