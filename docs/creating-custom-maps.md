---
title: Add a map
---

<span class="am-kicker">For contributors · about 20 min</span>

# Add a map

<p class="am-lede">One small XML file per map. We test it the way ATAK loads it before it ships to everyone. No time? <a href="https://github.com/joshuafuller/ATAK-Maps/issues/new">Request a map</a> instead.</p>

## Before you start

<div class="am-grid" markdown="0">
  <div class="am-card"><h3>Is it already here?</h3><p>Search the <a href="../maps/">map explorer</a> first.</p></div>
  <div class="am-card"><h3>May we use it?</h3><p>The source's terms must allow use in an app like ATAK. Government open data usually does.</p></div>
  <div class="am-card"><h3>Not OSM's own servers</h3><p><code>tile.openstreetmap.org</code> blocks ATAK. OSM-based styles on other servers are fine.</p></div>
</div>

## 1 · Find the tile URL

Open the map in a browser, press **F12**, open the **Network** tab and pan. Copy one image request and swap the numbers for placeholders:

| Placeholder | ATAK fills in |
|-------------|---------------|
| `{$z}` `{$x}` `{$y}` | Zoom, column and row. The usual `…/z/x/y.png` pattern. |
| `{$q}` | A quadkey, for Bing-style servers. |
| `{$serverpart}` | One of the values in `serverParts`, such as `a b c`. |

Requests with `service=WMS` and a `bbox` come from a WMS server: use the WMS form in the [XML reference](xml-reference.md).

## 2 · Write the XML

```xml
<customMapSource>
    <name>OpenTopoMap</name>        <!-- what ATAK shows -->
    <minZoom>1</minZoom>
    <maxZoom>17</maxZoom>              <!-- the server's deepest zoom -->
    <tileType>png</tileType>
    <serverParts>a b c</serverParts>
    <url>https://{$serverpart}.tile.opentopomap.org/{$z}/{$x}/{$y}.png</url>
</customMapSource>
```

Every field, and the WMS and layer-stack forms, are in the [XML reference](xml-reference.md).

## 3 · Name and place it

Screen space in ATAK is tight, so names stay short: **about 20 characters**.

| Map | Name | File |
|-----|------|------|
| Most maps | `USGS Topo` | `maps/base/usgs/usgs_topo.xml` |
| Non-US national | `DE Basemap Color` | `maps/base/de-basemap/de_basemap_color.xml` |
| Overlay | `+ FEMA Flood` | `maps/overlays/grg_fema_flood.xml` |

## 4 · Describe it

Add an entry to `maps/descriptions.yml`. The map explorer uses it for the card and the filters. The **test point** is where the ATAK test checks for real tiles; regional maps need one.

```yaml
opentopo-opentopomap:
  category: Topographic
  text: "Topographic style over OSM with contours and hillshade, global."
  test_point: [40.7128, -74.0060]   # needed for regional maps
```

## 5 · Test like ATAK

```console
$ uv run python -m mapvalidator --harness . --only maps/base/opentopo/opentopomap.xml
ok   maps/base/opentopo/opentopomap.xml

1 maps, 0 errors
```

The test builds tile URLs with ATAK's own rules and its “TAK” user agent, then checks for real tiles at minZoom and maxZoom, blank, blocked and placeholder tiles, see-through overlays and the naming rules. A failure names the zoom and the cause, for example “maxZoom z18: blank tile”: lower `maxZoom` and run it again.

## 6 · Open a pull request

1. Title it `feat: add OpenTopoMap`.
2. CI runs the same ATAK test on your map and checks the XML.
3. After merge, the map ships in the next release and appears in the map explorer.

## ATAK gotchas

!!! warning "WMS: tileType is png or jpg"
    Anything else makes ATAK send `format=null`, and the server refuses.

!!! warning "maxZoom is the server's real limit"
    Too high and ATAK caches blank tiles at the deepest zoom.

!!! warning "Renaming breaks offline tiles"
    ATAK names its offline cache after the map. Pick the name once.

!!! warning "Overlays must be see-through PNG"
    An opaque “overlay” hides the base map under it.
