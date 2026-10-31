<!-- markdownlint-disable MD041 -- the small label sits above the page title -->
<span class="am-kicker">ATAK 5.1 or later</span>

# Install & fix

<p class="am-lede">Get maps into ATAK in under a minute, use them offline, and fix the problems people hit most.</p>

## Pick a way

<div class="am-grid" markdown="0">
  <a class="am-card am-card--accent" href="#one-tap-or-qr"><span class="am-kicker">Fastest · 1 min</span><span class="am-display">One tap or QR</span><p>On the device, or scan from a computer.</p></a>
  <a class="am-card" href="#manual-install"><span class="am-kicker">Control · 5 min</span><span class="am-display">Manual copy</span><p>Pick exact files. Needed for overlays on top.</p></a>
  <a class="am-card" href="#update-or-remove"><span class="am-kicker">Many devices</span><span class="am-display">Release ZIP</span><p>One file to hand out or side-load.</p></a>
</div>

## One tap or QR

<div class="am-grid" markdown="0">
  <div class="am-card">
    <h3>On the ATAK device</h3>
    <ol>
      <li>Open the <a href="../maps/">map explorer</a> in the device's browser.</li>
      <li>Pick a map, then tap <b>Add to ATAK</b>.</li>
      <li>ATAK opens and imports it. It shows in the map layer list.</li>
    </ol>
  </div>
  <div class="am-card">
    <h3>From a computer</h3>
    <div class="am-qr">
      <img src="../qr/_all-maps.png" alt="QR code that adds every map to ATAK" width="110" height="110">
      <span>Scan a map's QR code with the device camera. This one adds <b>every map</b> as one data package.</span>
    </div>
  </div>
</div>

!!! note "Good to know"
    One-tap import puts every map, overlays too, in the base map list. To draw a “+” overlay on top of another map, use [manual copy](#use-overlays).

## Manual install

Download single XML files from the [map explorer](../maps/), or `atak-maps.zip` from [Releases](https://github.com/joshuafuller/ATAK-Maps/releases/latest). Copy them to the device:

| File | Copy to |
|------|---------|
| Base maps | `atak/imagery/mobile/mapsources/` |
| “+” overlays | `atak/grg/` |

`atak/` is in the device's internal storage, usually `/sdcard` or `/storage/emulated/0`. `atak/mobac/mapsources/` also works for base maps. New files usually show at once; if not, restart ATAK.

## Use overlays

<div class="am-split" markdown>
![](assets/brand/illo-overlay.jpg){ alt="" }

<div markdown>
1. Copy the “+” map's XML to `atak/grg/`.
2. Pick any base map in ATAK.
3. Turn the overlay on in **Overlay Manager**.

Symbols too small? **Overlay Manager → Map Controls → Map Imagery Scaling**. Try overlays first in the [map explorer](../maps/?tab=overlays).
</div>
</div>

## Offline use

<div class="am-split" markdown>
![](assets/brand/illo-offline.jpg){ alt="" }

<div markdown>
ATAK keeps the tiles you view. To save an area before you lose signal:

1. Select the map in the map layer selector.
2. Open **Map Manager** and choose **Download**.
3. Draw the area and pick the zoom levels.

The [map explorer](../maps/) shows an estimate for the area on screen, for example “1,240 tiles · about 25 MB”.
</div>
</div>

## Update or remove

<div class="am-grid" markdown="0">
  <div class="am-card"><h3>Update</h3><p>Import the new package or ZIP again. It replaces the old files.</p></div>
  <div class="am-card"><h3>Remove</h3><p>Delete the package in the <b>Mission Package Tool</b>, or delete the XML files you copied.</p></div>
  <div class="am-card am-card--warn"><h3>Coming from v1?</h3><p>v2 renamed every map. ATAK keeps offline tiles under the old names, so download your areas again.</p></div>
</div>

## Fix a problem

<div class="am-fix-head" markdown="0">
  <img src="../assets/brand/illo-blank.jpg" alt="" width="120" height="120">
  <p>Pick what you see. Every map is tested weekly the way ATAK loads it, so first check its status in the <a href="../maps/">map explorer</a>.</p>
</div>

<div class="am-faq" markdown="0">
  <details class="am-q" name="fix">
    <summary><span class="am-q__icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M15 9l-6 6M9 9l6 6"/></svg></span><span class="am-q__t"><b>Map is blank or black</b><small>Wrong place, too far in, or the server is down</small></span><svg class="am-q__chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></summary>
    <div class="am-q__a">
      <ul>
        <li><b>Outside its region:</b> US, UK, DE, CA and PL maps only draw inside that country.</li>
        <li><b>Zoomed too far:</b> each map stops at its own deepest zoom. The explorer shows the range.</li>
        <li><b>Server down:</b> the map's card in the <a href="../maps/">explorer</a> says “Working in ATAK” or names the problem.</li>
      </ul>
    </div>
  </details>
  <details class="am-q" name="fix">
    <summary><span class="am-q__icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12"/><path d="M7 10l5 5 5-5"/><path d="M5 21h14"/></svg></span><span class="am-q__t"><b>Maps do not show after import</b><small>A restart or the wrong folder</small></span><svg class="am-q__chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></summary>
    <div class="am-q__a">
      <p>Restart ATAK. For manual installs, check the folder: base maps go in <code>atak/imagery/mobile/mapsources/</code>, not <code>atak/imagery/</code> itself. ATAK's log is under <b>Settings → Show Log</b>.</p>
    </div>
  </details>
  <details class="am-q" name="fix">
    <summary><span class="am-q__icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/></svg></span><span class="am-q__t"><b>Overlay replaces my map</b><small>It was imported as a base map</small></span><svg class="am-q__chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></summary>
    <div class="am-q__a">
      <p>One-tap import adds “+” maps as base maps. Move the XML to <code>atak/grg/</code> and restart ATAK; it then shows in <b>Overlay Manager</b> on top of any base map. <a href="#use-overlays">How overlays work</a>.</p>
    </div>
  </details>
  <details class="am-q" name="fix">
    <summary><span class="am-q__icon"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="8" cy="15" r="4"/><path d="M10.8 12.2L20 3M17 6l3 3M14 9l2 2"/></svg></span><span class="am-q__t"><b>UK OS map needs a key</b><small>Free key from the OS Data Hub</small></span><svg class="am-q__chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></summary>
    <div class="am-q__a">
      <p>Get a free key from the OS Data Hub. Download the map's XML from the <a href="../maps/?region=UK">explorer</a>, replace <code>API_KEY_HERE</code> with your key, then copy it to the device.</p>
    </div>
  </details>
  <details class="am-q" name="fix">
    <summary><span class="am-q__icon"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/></svg></span><span class="am-q__t"><b>Where is OpenStreetMap?</b><small>Its main servers block ATAK</small></span><svg class="am-q__chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></summary>
    <div class="am-q__a">
      <p>The main OpenStreetMap tile servers block ATAK, so we do not include them. OSM-based maps on other servers work: OpenTopoMap, CyclOSM and OpenSeaMap.</p>
    </div>
  </details>
  <details class="am-q" name="fix">
    <summary><span class="am-q__icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/></svg></span><span class="am-q__t"><b>Which files does ATAK read?</b><small>.xml, .xmle and .bsh</small></span><svg class="am-q__chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></summary>
    <div class="am-q__a">
      <p><code>.xml</code> map sources (what ATAK Maps provides), <code>.xmle</code> encrypted map sources and <code>.bsh</code> scripted map sources.</p>
    </div>
  </details>
</div>

Still stuck? [Report a broken map](https://github.com/joshuafuller/ATAK-Maps/issues/new) or ask in [Discord](https://discord.gg/dQUYADMW87).
