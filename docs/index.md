---
title: Map sources for ATAK
hide:
  - navigation
  - toc
---

<section class="am-hero" markdown="0">
  <div class="am-hero-row">
    <div>
      <span class="am-kicker">Map sources for ATAK 5.1+</span>
      <h1>Find a map. Tap once. It is in ATAK.</h1>
      <p class="am-lede">Satellite, topo, street, nautical and overlay maps, each tested the way ATAK loads tiles.</p>
      <form class="am-search" role="search" action="maps/" method="get">
        <label>Search maps
          <input type="search" name="q" placeholder="Name, provider or type">
        </label>
        <label>Region
          <select name="region">
            <option value="Anywhere">Anywhere</option>
            <option value="Global">Global</option>
            <option value="US">United States</option>
            <option value="UK">United Kingdom</option>
            <option value="DE">Germany</option>
            <option value="CA">Canada</option>
            <option value="PL">Poland</option>
            <option value="Europe">Europe</option>
          </select>
        </label>
        <button type="submit">Show maps</button>
      </form>
    </div>
    <aside class="am-hero-all" aria-label="Add every map">
      <p class="am-display">Want them all?</p>
      <div class="am-qr">
        <img src="qr/_all-maps.png" alt="QR code that adds every map to ATAK" width="110" height="110">
        <span><b>On a computer:</b> scan with your ATAK device.</span>
      </div>
      <p><a class="am-btn am-btn--ghost" href="maps/?add=all">On the device: add all maps</a></p>
      <p>One data package. Remove it any time in the Mission Package Tool.</p>
    </aside>
  </div>
</section>

<span class="am-kicker">Or browse by type</span>

<div class="am-types" markdown="0">
  <a href="maps/?q=Satellite" style="--c:#4FA37A">Satellite</a>
  <a href="maps/?q=Topographic" style="--c:#C48A4E">Topographic</a>
  <a href="maps/?q=Street" style="--c:#8D9BAA">Street</a>
  <a href="maps/?q=Nautical" style="--c:#4F94D4">Nautical</a>
  <a href="maps/?q=Cycling" style="--c:#A483CC">Cycling</a>
  <a href="maps/?tab=overlays" style="--c:#FF7A2F">Overlays</a>
</div>

<span class="am-kicker" style="margin-top:2rem">Something not right?</span>

<div class="am-grid" markdown="0">
  <a class="am-card" href="install-guide/#fix-a-problem"><span class="am-display">Map is blank</span><p>Zoom limits, regional maps and tiles that need a key.</p></a>
  <a class="am-card" href="install-guide/#use-overlays"><span class="am-display">Overlay hides my map</span><p>“+” maps go in atak/grg/ to sit on top of a base map.</p></a>
  <a class="am-card" href="install-guide/#offline-use"><span class="am-display">Use maps offline</span><p>Download an area before you lose signal.</p></a>
</div>
