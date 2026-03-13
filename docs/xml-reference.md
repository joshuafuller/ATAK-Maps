# MOBAC XML Reference

## Overview

ATAK loads map tile sources from XML files originally defined by the
[Mobile Atlas Creator (MOBAC)](https://mobac.sourceforge.io/) project.
ATAK's UI labels these sources "Legacy" but the format is fully supported,
widely used, and the primary way community map sources are distributed.

Three XML root element types are recognized by ATAK's parser
(`MobacMapSourceFactory.java`):

| Root element | Purpose | Typical use case |
|---|---|---|
| `customMapSource` | TMS / XYZ / quadkey tile servers | Most web tile services (OSM, Google, Bing, ESRI) |
| `customWmsMapSource` | OGC Web Map Service (WMS) | Government GIS servers, ArcGIS WMS endpoints |
| `customMultiLayerMapSource` | Composite of other sources | Overlay combinations (e.g., satellite + road labels) |

Each XML file must contain exactly one root element.  The file extension must
be `.xml` (case-insensitive).

---

## customMapSource (TMS/XYZ Tiles)

Used for standard slippy-map tile servers that serve pre-rendered image tiles
addressed by zoom/x/y or quadkey.

### Element reference

| Element | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | **yes** | -- | Display name shown in ATAK map source list |
| `url` | string | **yes** | -- | Tile URL template with [placeholders](#url-placeholders) |
| `maxZoom` | integer | **yes** | -- | Maximum zoom level (inclusive) |
| `minZoom` | integer | no | `0` | Minimum zoom level (inclusive) |
| `tileType` | string | no | *none* | Image format hint (e.g., `png`, `jpg`). Not validated by parser. |
| `tileUpdate` | string/integer | no | `0` | [Cache control](#cache-control) value |
| `serverParts` | string | no | *none* | Whitespace-separated list for [load balancing](#server-load-balancing-serverparts) |
| `invertYCoordinate` | boolean | no | `false` | Set `true` for TMS servers that use inverted Y (origin at bottom-left) |
| `backgroundColor` | hex color | no | `#000000` | Background color as `#RRGGBB` |
| `coordinatesystem` | string | no | `EPSG:3857` | [Coordinate system](#coordinate-systems) identifier |

### Full annotated example

From [`opentopo/opentopo_opentopomap.xml`](../opentopo/opentopo_opentopomap.xml):

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<customMapSource>
    <name>OpenTopo - Opentopomap</name>
    <minZoom>1</minZoom>
    <maxZoom>17</maxZoom>
    <tileType>png</tileType>
    <tileUpdate>IfNoneMatch</tileUpdate>
    <serverParts>a b c</serverParts>
    <url>https://{$serverpart}.tile.opentopomap.org/{$z}/{$x}/{$y}.png</url>
</customMapSource>
```

**Element-by-element:**

- **`name`** -- The string displayed in ATAK's map source selector.  Can
  contain any characters including spaces, accented letters, and punctuation.
- **`url`** -- The tile URL template.  `{$serverpart}` is replaced by one of
  the values from `serverParts` on each request.  `{$z}`, `{$x}`, `{$y}` are
  replaced with standard tile coordinates.  HTML entities (e.g., `&amp;`) are
  unescaped by the parser.
- **`minZoom` / `maxZoom`** -- Integer zoom level bounds.  Tiles will not be
  requested outside this range.  `maxZoom` is required; if missing, parsing
  fails.
- **`tileType`** -- Informational tile format.  The parser stores it as-is;
  it does not affect request behavior for `customMapSource`.
- **`tileUpdate`** -- See [Cache Control](#cache-control).  `IfNoneMatch` is a
  string value that does not match the `\d+` regex, so refreshInterval stays
  at `0`.  It is only meaningful to downstream cache logic.
- **`serverParts`** -- See [Server Load Balancing](#server-load-balancing-serverparts).
- **`invertYCoordinate`** -- Must be the exact string `true` to enable
  (case-sensitive).  Flips the Y tile coordinate: `y = (2^zoom - 1) - y`.
  Needed for some TMS servers where row 0 is at the bottom.
- **`backgroundColor`** -- Hex color string.  The parser regex `#[0-9A-Fa-f]`
  is checked but the actual parsing expects at least 6 hex digits after `#` for
  a meaningful value.  In practice, always use `#000000` or `#FFFFFF`.

### Quadkey example

From [`Bing/Bing_Maps.xml`](../Bing/Bing_Maps.xml):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>Bing - Maps</name>
    <minZoom>0</minZoom>
    <maxZoom>20</maxZoom>
    <tileType>png</tileType>
    <tileUpdate>None</tileUpdate>
    <url>https://r0.ortho.tiles.virtualearth.net/tiles/r{$q}.png?g=45</url>
    <backgroundColor>#000000</backgroundColor>
</customMapSource>
```

The `{$q}` placeholder produces a Bing-style quadkey string.  See
[URL Placeholders](#url-placeholders) for the algorithm.

---

## customWmsMapSource (Web Map Service)

Used for OGC WMS endpoints.  ATAK constructs the full `GetMap` query string
automatically -- you provide only the base URL and layer configuration.

### Element reference

| Element | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | **yes** | -- | Display name |
| `url` | string | **yes** | -- | WMS base URL (up to and including `?` or ending before query params) |
| `layers` | string | **yes** | -- | WMS layer name(s), comma-separated |
| `maxZoom` | integer | **yes** | -- | Maximum zoom level |
| `tileType` | string | **yes** | -- | `PNG` or `JPG` -- mapped to WMS `FORMAT` MIME type |
| `minZoom` | integer | no | `-1` | Minimum zoom level (note: defaults to -1, not 0) |
| `styles` | string | no | `""` (empty) | WMS `STYLES` parameter value |
| `version` | string | no | `1.1.1` | WMS version (`1.1.1`, `1.3.0`, or `1.3.1`) |
| `coordinatesystem` | string | no | `EPSG:4326` | [Coordinate system](#coordinate-systems) (note: WMS default is 4326, not 3857) |
| `aditionalparameters` | string | no | `""` (empty) | Extra query string appended verbatim to the GetMap URL |
| `additionalparameters` | string | no | `""` (empty) | Alternate (correct) spelling -- both accepted |
| `backgroundColor` | hex color | no | `#000000` | Background color |
| `north`, `south`, `east`, `west` | decimal | no | *none* | Geographic bounds (all four must be present to take effect) |
| `tileUpdate` | string/integer | no | `0` | [Cache control](#cache-control) value |

### WMS version differences

The `version` element controls how ATAK builds the GetMap URL:

| Version | CRS parameter | SRID 4326 value | Axis order |
|---|---|---|---|
| `1.1.1` (default) | `srs=EPSG:4326` | `EPSG:4326` | x,y |
| `1.3.0` | `crs=CRS:84` (when SRID is 4326) | `CRS:84` | x,y |
| `1.3.1` | `crs=CRS:84` (when SRID is 4326) | `CRS:84` | x,y |

For SRIDs other than 4326 with WMS 1.3.x, the parameter is `crs=EPSG:<srid>`.

ATAK always emits the `bbox` in west,south,east,north order regardless of
version (which is technically non-compliant for WMS 1.3.0 with EPSG:4326, but
works because ATAK uses `CRS:84` instead).

### Generated query parameters

ATAK appends these parameters to the URL (in order):

1. `service=WMS&request=GetMap&layers=<layers>&srs=EPSG:<srid>` (or `crs=...` for 1.3.x)
2. `&format=<mime>&width=256&height=256`
3. `&version=<version>`
4. `&styles=<styles>` (empty string if not specified)
5. The `aditionalparameters` / `additionalparameters` value (appended verbatim)
6. `&bbox=<west>,<south>,<east>,<north>`

### CDATA usage

WMS URLs and additional parameters often contain `&` and other XML-special
characters.  Wrap them in `<![CDATA[...]]>` to avoid escaping issues:

```xml
<url><![CDATA[https://hazards.fema.gov:443/arcgis/services/public/NFHLWMS/MapServer/WMSServer?]]></url>
<aditionalparameters><![CDATA[&TRANSPARENT=TRUE&STYLES=default]]></aditionalparameters>
```

Alternatively, use XML entities (`&amp;` for `&`).

### Full annotated example

From [`basemapDE/basemap.de Raster Farbe.xml`](../basemapDE/basemap.de%20Raster%20Farbe.xml):

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<customWmsMapSource>
    <name>basemap.de Raster, Farbe</name>
    <minZoom>0</minZoom>
    <maxZoom>19</maxZoom>
    <tileType>PNG</tileType>
    <version>1.3.0</version>
    <layers>de_basemapde_web_raster_farbe</layers>
    <url><![CDATA[https://sgx.geodatenzentrum.de/wms_basemapde?]]></url>
    <coordinatesystem>EPSG:3857</coordinatesystem>
    <aditionalparameters><![CDATA[]]></aditionalparameters>
    <backgroundColor>#000000</backgroundColor>
</customWmsMapSource>
```

### WMS example with additional parameters

From [`GRG/grg_FEMA_NFHL_Flood_Hazard_Zones.xml`](../GRG/grg_FEMA_NFHL_Flood_Hazard_Zones.xml):

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<customWmsMapSource>
    <name>FEMA NFHL - Flood Hazard Zones (WMS)</name>
    <minZoom>5</minZoom>
    <maxZoom>19</maxZoom>
    <tileType>PNG</tileType>
    <version>1.3.0</version>
    <layers>12</layers>
    <url><![CDATA[https://hazards.fema.gov:443/arcgis/services/public/NFHLWMS/MapServer/WMSServer?]]></url>
    <coordinatesystem>EPSG:4326</coordinatesystem>
    <aditionalparameters><![CDATA[&TRANSPARENT=TRUE&STYLES=default]]></aditionalparameters>
    <backgroundColor>#000000</backgroundColor>
</customWmsMapSource>
```

### tileType mapping

The `tileType` value is uppercased by the parser and mapped to a WMS
`FORMAT` MIME type:

| tileType (case-insensitive) | WMS FORMAT |
|---|---|
| `PNG` | `image/png` |
| `JPG` | `image/jpeg` |

Other values will produce a `null` format MIME, which will break WMS requests.
Always use `PNG` or `JPG`.

---

## customMultiLayerMapSource (Composite Layers)

Composites multiple map sources into a single tile by drawing them on an
Android `Canvas` and outputting the result as PNG.

### Element reference

| Element | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | **yes** | -- | Display name |
| `layers` | container | **yes** | -- | Contains child `customMapSource`, `customWmsMapSource`, or `customMultiLayerMapSource` elements |
| `backgroundColor` | hex color | no | `#000000` | Background fill color drawn first |
| `layersAlpha` | string | no | all `1.0` | Space-separated opacity values (0.0--1.0), one per layer |

### How compositing works

1. A 256x256 ARGB bitmap is created.
2. The `backgroundColor` is drawn as a solid fill.
3. Each child layer's tile is loaded and drawn in order (first layer on bottom).
4. If `layersAlpha` is specified, each layer is drawn with the corresponding
   alpha value (0.0 = fully transparent, 1.0 = fully opaque).
5. The composite is compressed to PNG format at quality 80.

All child layers **must** use the same SRID.  If they differ, construction
throws `IllegalArgumentException`.

The composite's zoom range is the union of all child layers' zoom ranges
(min of all minZooms, max of all maxZooms).  At any given zoom level, child
layers outside their own zoom range are simply skipped.

### Validation rules

- `name` is required; missing name throws `RuntimeException`.
- If `layersAlpha` is specified, the number of alpha values **must** equal the
  number of child layers.  A mismatch throws `RuntimeException`.
- At least one child layer must be present in `layers`.

### Full annotated example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<customMultiLayerMapSource>
    <name>Satellite with Road Overlay</name>
    <backgroundColor>#000000</backgroundColor>
    <layersAlpha>1.0 0.7</layersAlpha>
    <layers>
        <customMapSource>
            <name>Satellite Base</name>
            <minZoom>0</minZoom>
            <maxZoom>19</maxZoom>
            <tileType>jpg</tileType>
            <url>https://example.com/sat/{$z}/{$x}/{$y}.jpg</url>
        </customMapSource>
        <customMapSource>
            <name>Road Overlay</name>
            <minZoom>0</minZoom>
            <maxZoom>19</maxZoom>
            <tileType>png</tileType>
            <url>https://example.com/roads/{$z}/{$x}/{$y}.png</url>
        </customMapSource>
    </layers>
</customMultiLayerMapSource>
```

The second layer (Road Overlay) is drawn at 70% opacity over the satellite
base.  The `layers` container can hold any mix of the three source types,
including nested `customMultiLayerMapSource` elements.

---

## URL Placeholders

The following placeholders are replaced in `customMapSource` URLs at tile
load time:

| Placeholder | Replaced with | Example |
|---|---|---|
| `{$z}` | Zoom level (integer) | `14` |
| `{$x}` | Tile column (integer) | `8567` |
| `{$y}` | Tile row (integer, top-left origin unless `invertYCoordinate` is true) | `5765` |
| `{$q}` | Bing-style quadkey string | `12031021230` |
| `{$serverpart}` | Next value from `serverParts` (round-robin) | `a` |

### Quadkey algorithm

The `{$q}` placeholder produces a quadkey string of length equal to the zoom
level.  For each bit position from zoom down to 1:

1. Start with digit `0`.
2. If the corresponding bit in `x` is set, add 1.
3. If the corresponding bit in `y` is set, add 2.
4. Append the resulting digit (0, 1, 2, or 3) to the string.

At zoom level 3, tile (6, 2) produces quadkey `"210"`:

| Bit position | x bit | y bit | Digit |
|---|---|---|---|
| 2 (mask=4) | 1 | 0 | 1 |
| 1 (mask=2) | 1 | 1 | 3 |
| 0 (mask=1) | 0 | 0 | 0 |

Result: `"130"`.

This is the standard [Bing Maps tile system](https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system)
quadkey encoding.

---

## Server Load Balancing (serverParts)

The `serverParts` element distributes tile requests across multiple server
hostnames.  Values are substituted into the `{$serverpart}` placeholder in
round-robin order (synchronized across threads).

**The parser splits on whitespace only** (`\\s+` regex).  Values separated by
commas without spaces are treated as a single server part.

### Examples from this repository

**Space-separated subdomains** (correct usage):

```xml
<!-- From opentopo_opentopomap.xml -->
<serverParts>a b c</serverParts>
<url>https://{$serverpart}.tile.opentopomap.org/{$z}/{$x}/{$y}.png</url>
```

Cycles through: `a`, `b`, `c`

**Space-separated numbers**:

```xml
<!-- From michelin_osm_michelin.xml -->
<serverParts>1 2 3 4</serverParts>
<url>https://map{$serverpart}.viamichelin.com/...</url>
```

Cycles through: `1`, `2`, `3`, `4`

**Comma-separated -- treated as a single value**:

```xml
<!-- From openseamap_base_chart.xml -->
<serverParts>t1,t2,t3</serverParts>
```

This produces a **single** server part with the literal value `t1,t2,t3`.
Since the URL in this file uses a hardcoded hostname (`t2.openseamap.org`)
rather than `{$serverpart}`, this has no practical effect.  If you intended
load balancing, use spaces: `t1 t2 t3`.

**Empty element** -- equivalent to omitting it:

```xml
<serverParts></serverParts>
```

An empty or whitespace-only value is ignored (the trim/length check prevents
splitting).

---

## Coordinate Systems

The `coordinatesystem` element sets the spatial reference ID (SRID) for the
map source.

| SRID | Name | Notes |
|---|---|---|
| `EPSG:3857` | Web Mercator | Default for `customMapSource`.  Standard for web tile services. |
| `EPSG:4326` | WGS 84 | Default for `customWmsMapSource`.  Geographic lat/lon coordinates. |
| `EPSG:900913` | Web Mercator (legacy) | Alias for 3857.  ATAK translates this internally via `WebMercatorProjection`. |

**Format:** Must match the regex `EPSG:\d+` exactly.  Values like `epsg:3857`
or `EPSG:3857 ` (trailing space) will be silently ignored, leaving the default
in effect.

### Element name casing

The parser matches **only** `coordinatesystem` (all lowercase).  The camelCase
variant `coordinateSystem` is **not** recognized by the parser and will be
silently ignored, leaving the default SRID in effect.

> **Note:** The repo's XSD schema accepts both spellings for compatibility with
> existing XML files, but only the lowercase version has any effect in ATAK.

---

## Cache Control

The `tileUpdate` element controls how aggressively ATAK refreshes cached tiles.

The parser applies the regex `\d+` -- only purely numeric strings are
recognized.  Non-numeric values are silently ignored.

| Value | Meaning |
|---|---|
| `0` (or omitted) | Never auto-refresh.  Tiles are cached indefinitely in ATAK's SQLite tile database. |
| Any positive integer | Refresh interval in milliseconds (e.g., `604800000` = 1 week). |
| `None` | Not numeric -- ignored by parser.  Equivalent to `0`. |
| `IfNoneMatch` | Not numeric -- ignored by parser.  Equivalent to `0`. |

In practice, most sources in this repository use `None` or `IfNoneMatch`, both
of which result in the default `refreshInterval = 0` (no automatic refresh).

The values `None` and `IfNoneMatch` may have meaning in the original MOBAC
desktop application, but ATAK's parser does not act on them.

---

## HTTP Behavior

When ATAK fetches a tile, the following HTTP settings are applied
(from `CustomMobacMapSource.configureConnection()`):

| Setting | Value | Configurable? |
|---|---|---|
| `User-Agent` header | `TAK` | No (hardcoded) |
| `x-common-site-name` header | Value of `name` element | Automatic |
| Connect timeout | 3,000 ms | Only via `Config` object (not XML) |
| Read timeout | 5,000 ms | Only via `Config` object (not XML) |
| Caching | `setUseCaches(true)` | No |

### SSL / TLS

For HTTPS URLs, ATAK checks its internal certificate database
(`AtakCertificateDatabase`) for a CA certificate matching the server hostname.
If found, a custom `SSLSocketFactory` is configured with that trust store,
allowing connections to servers with custom/private CA certificates.

### Authentication

ATAK uses `AtakAuthenticationHandlerHTTP` for HTTP authentication, which
supports up to 5 authentication retries.  If the server returns HTTP 401
(Unauthorized) or 403 (Forbidden), the source is marked as auth-failed and
no further tile requests are made until `clearAuthFailed()` is called
(typically via ATAK's connectivity check mechanism).

### Custom HTTP headers

There is **no way** to add custom HTTP headers via the XML file.  The only
headers sent are `User-Agent: TAK` and `x-common-site-name: <name>`, plus
any headers added by the JVM's HTTP stack (Accept, Host, Connection, etc.).

---

## Known Quirks

### `aditionalparameters` is a typo -- and it's what the parser looks for

The WMS parser checks for both `aditionalparameters` (with one `d`) and
`additionalparameters` (correctly spelled).  Either works.  The misspelled
version comes from the original MOBAC project.  Most existing WMS files in
the wild use the misspelled version.

Source: `MobacMapSourceFactory.java` line 380-381:
```java
} else if (inTag.equals("additionalparameters")
        || inTag.equals("aditionalparameters"))
```

### `coordinatesystem` vs `coordinateSystem`

Only `coordinatesystem` (all lowercase) is recognized by the parser.  The
camelCase variant `coordinateSystem` is silently ignored.  Some files in
this repository use the wrong casing (e.g.,
[`openseamap/openseamap_base_chart.xml`](../openseamap/openseamap_base_chart.xml)),
which means their coordinate system setting has no effect and the default
SRID applies instead.

### `tileUpdate` accepts both string values and integers -- but only integers have effect

The parser regex `\d+` only matches purely numeric strings.  String values
like `None` and `IfNoneMatch` are silently discarded, resulting in the default
`refreshInterval = 0`.

### backgroundColor regex is too restrictive

The parser regex `#[0-9A-Fa-f]` matches only `#` followed by a **single** hex
digit.  A standard 6-digit color like `#000000` has 6 hex digits after `#`,
which does not match this single-character regex.  This means
`backgroundColor` is effectively **never parsed** from XML in practice --
the value always falls through to the default `0` (transparent black).

### Tile size is always 256

The tile size is hardcoded to 256 pixels in the factory (`parseCustomMapSource`
passes `256` directly).  There is no XML element to change it.

### `tileType` is not validated for customMapSource

For `customMapSource`, the `tileType` value is stored as-is and is not used to
determine request behavior.  For `customWmsMapSource`, it is uppercased and
mapped to a MIME type (`PNG` to `image/png`, `JPG` to `image/jpeg`).

### `ignoreErrors` is not parsed by ATAK

The `ignoreErrors` element appears in some XML files inherited from MOBAC, but
ATAK's parser does not look for or act on it.  The XSD schema accepts it for
compatibility.

### Entity references are rejected

The parser throws `IOException("Entity Reference Error")` if it encounters an
XML entity reference (e.g., `&custom;`).  Standard XML entities like `&amp;`
are handled by the XML parser itself before this check, so they work fine.
Custom entity definitions will cause parsing to fail.

### WMS URL fixup

ATAK automatically appends `?` or `&` to WMS URLs as needed.  If your URL
has no query string, `?` is appended.  If it has a query string that doesn't
end with `&`, one is appended.  You can include the trailing `?` in your URL
(as most examples do) or omit it.

---

## Quick Reference Table

All elements across all three root types, with which types they belong to:

| Element | customMapSource | customWmsMapSource | customMultiLayerMapSource | Description |
|---|---|---|---|---|
| `name` | required | required | required | Display name |
| `url` | required | required | -- | Tile URL template or WMS base URL |
| `maxZoom` | required | required | *derived* | Maximum zoom level |
| `minZoom` | optional (default 0) | optional (default -1) | *derived* | Minimum zoom level |
| `tileType` | optional | required | *always PNG* | Image format |
| `layers` | -- | required | -- | WMS layer name(s) |
| `layers` (container) | -- | -- | required | Child map source elements |
| `tileUpdate` | optional | optional | -- | Cache refresh interval |
| `serverParts` | optional | -- | -- | Load balancing server list |
| `invertYCoordinate` | optional | -- | -- | Flip Y axis for TMS |
| `backgroundColor` | optional | optional | optional | Background fill color |
| `coordinatesystem` | optional (default 3857) | optional (default 4326) | -- | Spatial reference |
| `styles` | -- | optional | -- | WMS styles parameter |
| `version` | -- | optional (default 1.1.1) | -- | WMS version |
| `aditionalparameters` | -- | optional | -- | Extra WMS query params |
| `additionalparameters` | -- | optional | -- | Same as above (alt spelling) |
| `north` / `south` / `east` / `west` | -- | optional | -- | Geographic bounds |
| `layersAlpha` | -- | -- | optional | Per-layer opacity values |
| `ignoreErrors` | *ignored* | *ignored* | -- | MOBAC element, not parsed by ATAK |

---

## Validation

This repository includes an XSD schema at [`schema/mobac-maps.xsd`](../schema/mobac-maps.xsd)
that validates all three XML root element types.  CI validates every XML file
in the repository against this schema on pull requests.

To validate locally:

```bash
xmllint --noout --schema schema/mobac-maps.xsd path/to/source.xml
```
