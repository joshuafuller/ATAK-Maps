# ATAK-Maps GitHub Pages Site — Design

**Date:** 2026-07-13
**Status:** Approved (pending spec review)
**Issue:** #81 (QR-code install) — expanded into a full documentation + install site

## Goal

Publish a GitHub Pages site for ATAK-Maps that makes installing a map into
ATAK effortless: every map gets a scannable **QR code** and a tappable
**"Add to ATAK"** button, alongside the existing documentation. The site
auto-updates from the repository's XML map sources.

## Why a site (not just the README)

GitHub's markdown sanitizer strips `tak://` links, so a tappable "Add to
ATAK" link is impossible in the README. On a real hosted `https` page,
browsers honour custom URI schemes, so `<a href="tak://…">` works and hands
off to ATAK on-device. The site is the only place the tappable link can
actually live. The README keeps a bundle QR image (which works anywhere,
being just an image) plus a prominent link to the site.

## The ATAK import mechanism (established via research)

ATAK 5.1+ handles `tak://com.atakmap.app/import?url=<url-encoded URL>` from a
text QR or a link. On activation it shows a confirm dialog, downloads the
file at `url`, and runs it through the import framework
(`ImportExportMapComponent.beginImport`). Map sources are a documented use
case. QRTAK (`joshuafuller/qrtak`) already generates these import URIs; this
project reuses the same URI format.

## Architecture

Four cooperating pieces, each independently testable:

### 1. Import-URI builder (pure, unit-tested)

A single pure function turns a public file URL into the ATAK import URI:

```
build_import_uri(download_url) -> "tak://com.atakmap.app/import?url=<percent-encoded download_url>"
```

This is the correctness-critical unit — a malformed URI silently fails to
import. It gets RED-first tests and a mutation check (repo TDD norm). Lives
in an importable module (`mapvalidator/qr.py`) so tests can import it.

### 2. Catalog generator (`scripts/gen_pages_catalog.py`)

Reuses the XML discovery/parsing already in
`.github/scripts/generate-catalog.py` (`find_xml_files`, `SOURCE_TYPE_MAP`).
For every map source it produces:

- a **QR PNG** (`docs/qr/<slug>.png`) encoding the map's import URI, via
  `qrcode[pil]`. The `docs/qr/` directory and `docs/maps.md` are **generated
  and git-ignored** — rebuilt on every site build so they never drift;
- an entry on a generated **Maps** page (`docs/maps.md`) with: name,
  provider (directory), source type, the QR image, a tappable **Add to
  ATAK** link, a **raw download** link, and any per-source note (e.g.
  "requires a free API key" for the Ordnance Survey sources).

Slug = provider + filename stem, lowercased, non-alphanumerics collapsed to
`-` (stable, filename-safe).

### 3. Per-map import target

The import `url` for each map points at the map's raw file on
`raw.githubusercontent.com/joshuafuller/ATAK-Maps/master/<path>` (stable,
already served, no build step). **Validation gate:** confirm on-device that
ATAK imports a raw `.xml` map source from that URL. If it does not, the
documented contingency is to have the catalog generator emit a proper
per-map ATAK **data package** (`.zip` containing `MANIFEST/manifest.xml` +
the XML), host it in the site output, and point the import URI there — data
packages are the guaranteed-supported format. Raw-XML-first keeps it simple;
escalate only if validation fails.

### 4. Bundle install + stable release asset

The landing page and README show a **bundle** QR + Add-to-ATAK for the whole
map set, pointing at a stable URL:
`https://github.com/joshuafuller/ATAK-Maps/releases/latest/download/atak-maps.zip`.

Today the release asset is versioned (`atak-maps-<version>.zip`), so this
URL does not resolve. Fix: change the `@semantic-release/github` asset
`name`/`label` in `.releaserc.json` to the constant `atak-maps.zip`. Every
release then publishes that name, making the `latest/download` URL stable and
the bundle QR static. (The build already produces `dist/atak-maps.zip`.)

## MkDocs Material site

- `mkdocs.yml` at repo root: Material theme, site/repo URLs, logo/favicon
  from `images/ATAK_MAPS_Logo.png`, search enabled, explicit `nav`.
- `docs_dir: docs`. Reuses existing `docs/*.md` (install-guide,
  creating-custom-maps, xml-reference, release-guide) as site pages.
- New `docs/index.md`: hero, "install in 30 seconds", link to Maps.
- Generated `docs/maps.md` (from piece 2) — **generated file, git-ignored**;
  built fresh in CI so it never drifts.
- `exclude_docs` drops `superpowers/**` from the build. `mkdocs build
  --strict` in CI catches broken links / nav.

## Deployment

`.github/workflows/pages.yml`: on push to `master` and `workflow_dispatch` —
set up Python + uv, install `mkdocs-material` + `qrcode[pil]`, run
`gen_pages_catalog.py`, `mkdocs build --strict`, `actions/upload-pages-artifact`,
`actions/deploy-pages`. Pages source set to **GitHub Actions**. Concurrency
guard so overlapping deploys cancel.

## README changes

New "Add to ATAK" section: bundle QR image + the `tak://…` bundle URI as a
copy-paste code line (honestly noted as not-clickable on GitHub) + a
prominent link to the Pages site for per-map, tappable install. Unlike the
per-map QRs, the bundle QR PNG is **committed** to the repo (e.g.
`images/add-to-atak.png`) — GitHub renders the README directly, not through
the MkDocs build, so it needs a real file. Its content is static (the bundle
URL never changes), so it is generated once and committed.

## Dependencies (pinned, build/dev only)

- `mkdocs-material` — site generator.
- `qrcode[pil]` — QR PNG generation.

Both are build-time only (not shipped, not needed by the validator). Added to
a dev/docs dependency group, pinned, per the repo's minimal-imports stance.

## Testing

- **Unit (pytest, repo style):** `build_import_uri` (scheme + percent-encoding,
  RED-first + mutation-checked); catalog helpers — slug generation, per-map
  entry fields, key-gated note detection.
- **Build gate:** `mkdocs build --strict` fails CI on broken links/nav.
- **Manual validation gate:** after cutting the next release tag (which
  produces `atak-maps.zip`), scan the bundle QR and a per-map QR on an
  ATAK 5.1+ device and confirm the import prompt installs the map(s). This
  resolves the raw-XML-vs-data-package question.

## Sequencing

1. Import-URI builder + tests.
2. Catalog generator + QR generation + tests.
3. MkDocs site (config, index, nav) + README section + `.releaserc.json`
   constant asset.
4. Pages deploy workflow; enable Pages (Actions source).
5. Merge → cut a new release tag (includes the recently merged BLM /
   BC-Wildfire / Ordnance Survey maps) → stable `atak-maps.zip` exists.
6. On-device validation; escalate per-map to data packages only if raw XML
   is rejected.

## Non-goals

- Map preview thumbnails / screenshots (possible later).
- Search analytics, versioned docs, i18n.
- Changing map XML content or the existing validator/prober behaviour.

## Open risks

- **Raw-XML import** acceptance by ATAK — mitigated by the data-package
  contingency (piece 3).
- **Enabling Pages** requires a one-time repo setting (Actions as source) —
  done via `gh` API or repo settings.
- **`tak://` on the hosted site** — expected to work (browser honours the
  scheme); confirmed in the validation gate.
