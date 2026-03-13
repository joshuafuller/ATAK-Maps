# Installing ATAK Maps

## Quick Start

1. Download `atak-maps-<version>.zip` from the [Releases page](https://github.com/joshuafuller/ATAK-Maps/releases).
2. Open the ZIP in ATAK using **Import** — ATAK places the map files automatically.
3. New map sources appear in the map layer selector.

That's it. ATAK's Import feature handles file placement for you.

![Install Flow](images/install-flow.png)

## Using ATAK Import (Recommended)

The easiest way to install maps is through ATAK's built-in Import feature:

1. Download `atak-maps-<version>.zip` from the [Releases page](https://github.com/joshuafuller/ATAK-Maps/releases) onto your device.
2. In ATAK, tap **Import** (or use your file manager to open the ZIP with ATAK).
3. ATAK ingests the ZIP and the map sources populate automatically.
4. Check the map layer selector — new sources should be listed.

No manual file copying required. ATAK handles sorting base maps and overlays into the correct locations.

## What's in the Download

The release ZIP contains all available XML map source files, organized by provider:

- **Providers included:** Bing, Google, ESRI, USGS, OpenTopo, and others
- **Two types of files:**
  - **Base maps** — satellite imagery, street maps, topographic maps
  - **Overlays** — transparent layers (flood zones, trails, reference grids) with filenames starting with `grg_`

## Manual Installation (Alternative)

If you prefer to place files manually or want to install only specific maps:

![Directory Layout](images/directory-layout.png)

### Base Maps

Copy `.xml` files (anything **not** prefixed `grg_`) to:

```
<storage>/atak/imagery/mobile/mapsources/
```

`<storage>` is your device's internal storage root (typically `/sdcard` or `/storage/emulated/0`). The alternate directory `<storage>/atak/mobac/mapsources/` also works.

### Overlays

Copy files starting with `grg_` (found in the `GRG/` folder) to:

```
<storage>/atak/grg/
```

These appear as overlay layers in ATAK, not base maps.

### Verify

1. Open ATAK.
2. Tap the map layer selector (layers icon).
3. New map sources should be listed. Select one and confirm tiles load.
4. For overlays, check the overlay manager.

ATAK uses file system monitoring, so new map files may appear without restarting the app. If they don't show up, restart ATAK.

## Installing Individual Maps

You don't have to install the entire collection:

1. Browse the repository folders on [GitHub](https://github.com/joshuafuller/ATAK-Maps).
2. Download just the `.xml` files you want.
3. Either import them via ATAK, or manually place them in the directories above.

## Offline Caching

ATAK automatically caches map tiles you view. To proactively cache an area for offline use:

1. In ATAK, open the map layer selector and choose the map source you want to cache.
2. Navigate to **Map Manager** (or long-press on the map layer).
3. Select **Download** and draw a region on the map.
4. Choose the zoom levels you need and start the download.
5. Cached tiles are stored in SQLite databases on your device and persist when you go offline.

Once cached, those tiles are available with no internet connection.

## Troubleshooting

### Maps don't appear after import

- Try restarting ATAK.
- If using manual install, confirm files are in the correct directory.
- Check ATAK logs (Settings > Show Log) for errors loading map sources.

### Tiles show as black or blank

- The map server may be down or blocking requests.
- Check your internet connection.
- Some sources (notably OpenStreetMap) may restrict access from ATAK. These files are included for reference but may not always work.

### Wrong directory (manual install)

| File type | Correct directory | Common mistake |
|-----------|-------------------|----------------|
| Base maps (`.xml`) | `atak/imagery/mobile/mapsources/` | `atak/imagery/` (parent dir — won't be scanned) |
| Overlays (`grg_*.xml`) | `atak/grg/` | `atak/imagery/mobile/mapsources/` |

### Accepted file extensions

| Extension | Description |
|-----------|-------------|
| `.xml` | Standard map source (this is what ATAK-Maps provides) |
| `.xmle` | Encrypted XML map source |
| `.bsh` | BeanShell scripted map source |
