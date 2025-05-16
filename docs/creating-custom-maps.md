# Creating Custom Maps

This guide explains how to craft your own MOBAC XML files so they can be used within ATAK.

## Structure of a MOBAC XML File
A basic XML file in this repository uses the `<customMapSource>` element with several required tags:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
    <name>My Custom Map</name>
    <minZoom>0</minZoom>
    <maxZoom>18</maxZoom>
    <tileType>png</tileType>
    <tileUpdate>None</tileUpdate>
    <url>https://myserver.example.com/tiles/{$z}/{$x}/{$y}.png</url>
    <backgroundColor>#000000</backgroundColor>
</customMapSource>
```

* **name** – Display name inside ATAK.
* **minZoom** and **maxZoom** – Lowest and highest zoom levels supported by your map server.
* **tileType** – Usually `png` or `jpg` depending on the server output.
* **tileUpdate** – Leave as `None` unless the server provides versioning.
* **url** – Tile endpoint using placeholders like `{$z}`, `{$x}`, and `{$y}` or the `{$q}` quadkey.
* **backgroundColor** – Color used when tiles are missing.

## Selecting Tile Server URLs and Zoom Levels

Choose a tile server that allows access from third‑party applications. Many providers document their tile URL format and the zoom ranges they support. Insert the URL in the `<url>` tag and adjust `<minZoom>` and `<maxZoom>` accordingly. Test several zoom levels to make sure imagery loads correctly without excessive requests.

## Testing XML Files in ATAK

1. Copy your XML file into the `ATAK/imagery` folder on your device.
2. Open ATAK and check the map list for the new entry.
3. Pan and zoom through different levels to ensure tiles load as expected.
4. If the map fails to load, verify the URL format and zoom range.
5. Once satisfied, you can submit the XML file to this repository following the [contribution guidelines](../CONTRIBUTING.md).

