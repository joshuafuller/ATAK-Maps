"""Check map sources the way ATAK uses them.

For every map the harness builds the exact tile URL ATAK requests
(atak_source.tile_url), fetches it with ATAK's User-Agent "TAK" at minZoom,
maxZoom and maxZoom + 1 over a test point where the map has data, and
classifies each response (tile_content.classify_tile). It also enforces the
naming and overlay rules in CLAUDE.md.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from mapvalidator.atak_source import AtakSource, parse_source, tile_for_point, tile_url
from mapvalidator.catalog import slugify
from mapvalidator.tile_content import TileVerdict, classify_tile

TAK_USER_AGENT = (
    "TAK"  # CustomMobacMapSource.java: conn.setRequestProperty("User-Agent", "TAK")
)
BROWSER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
DEFAULT_TEST_POINT = (40.7128, -74.0060)  # New York
MAX_NAME_LENGTH = 22
OVERLAY_DIR = "GRG"
_KEY_PLACEHOLDERS = ("API_KEY_HERE", "YOUR_API_KEY", "YOUR_KEY_HERE", "{key}")
_WMS_TILE_TYPES = ("JPG", "PNG")


@dataclass
class Response:
    status: int | None
    content_type: str | None
    body: bytes
    error: str | None


@dataclass
class Finding:
    level: str  # error | warn | info
    message: str


Fetch = Callable[[str, str], Response]


def _test_point(path: Path, root: Path) -> tuple[float, float]:
    desc_file = root / "descriptions.yml"
    if desc_file.exists():
        import yaml

        entry = (yaml.safe_load(desc_file.read_text()) or {}).get(
            slugify(f"{path.parent.name}-{path.stem}")
        ) or {}
        point = entry.get("test_point")
        if point:
            return float(point[0]), float(point[1])
    return DEFAULT_TEST_POINT


def _check_name(src: AtakSource, overlay: bool) -> list[Finding]:
    name = src.name or ""
    out = []
    if overlay and not name.startswith("+ "):
        out.append(Finding("error", f"overlay name '{name}' must start with '+ '"))
    if not overlay and name.startswith("+ "):
        out.append(
            Finding(
                "error",
                f"base map name '{name}' must not start with '+ ' (only overlays in GRG/)",
            )
        )
    if len(name) > MAX_NAME_LENGTH:
        out.append(
            Finding(
                "warn",
                f"name '{name}' is {len(name)} characters (keep it to {MAX_NAME_LENGTH})",
            )
        )
    return out


def _fetch_tile(
    src: AtakSource, z: int, point, fetch: Fetch, ua: str
) -> tuple[str, Response, TileVerdict | None]:
    x, y = tile_for_point(src, point[0], point[1], z)
    url = tile_url(src, z, x, y)
    resp = fetch(url, ua)
    if resp.error or resp.status != 200:
        return url, resp, None
    return url, resp, classify_tile(resp.body, resp.content_type)


def _problem(resp: Response, verdict: TileVerdict | None, overlay: bool) -> str | None:
    """Why this response is not usable map data, or None if it is."""
    if resp.error:
        return resp.error
    if verdict is None:
        return f"HTTP {resp.status}"
    if verdict.kind in ("error", "placeholder"):
        return f"{verdict.kind}: {verdict.detail}"
    if verdict.kind == "blank":
        return "blank tile (single opaque colour)"
    if verdict.kind == "empty" and not overlay:
        return "fully transparent tile (no data at the test point)"
    return None


def _check_zooms(
    src: AtakSource,
    label: str,
    point,
    fetch: Fetch,
    overlay: bool,
    empty_ok: bool,
    has_data: set[str],
) -> list[Finding]:
    """Check one leaf source; add "minZoom"/"maxZoom" to has_data where it drew something."""
    out = []
    for z, role in ((src.min_zoom, "minZoom"), (src.max_zoom, "maxZoom")):
        url, resp, verdict = _fetch_tile(src, z, point, fetch, TAK_USER_AGENT)
        if verdict is not None and verdict.kind == "image":
            has_data.add(role)
        problem = _problem(resp, verdict, empty_ok)
        if problem is None:
            opaque = (
                verdict is not None
                and verdict.kind == "image"
                and verdict.see_through_fraction == 0.0
            )
            if overlay and role == "maxZoom" and opaque:
                out.append(
                    Finding(
                        "error",
                        f"{label}overlay tile at z{z} is opaque; overlays must be transparent",
                    )
                )
            continue
        if not resp.error and (verdict is None or verdict.kind != "image"):
            b_url, b_resp, b_verdict = _fetch_tile(
                src, z, point, fetch, BROWSER_USER_AGENT
            )
            if b_verdict is not None and b_verdict.kind == "image":
                out.append(
                    Finding(
                        "error",
                        f"{label}z{z}: blocked for User-Agent TAK ({problem}); a browser gets a real tile",
                    )
                )
                break
        hint = (
            " (maxZoom is higher than the server's data)"
            if role == "maxZoom" and src.max_zoom > src.min_zoom
            else ""
        )
        # One colour at high zoom can be real (water, a roof) or a "no data"
        # fill, so it only warns there; at minZoom it is always wrong.
        level = (
            "warn"
            if role == "maxZoom" and verdict is not None and verdict.kind == "blank"
            else "error"
        )
        out.append(Finding(level, f"{label}{role} z{z}: {problem}{hint} — {url}"))
        if resp.error:
            break  # connection-level failure; other zooms will fail the same way
    else:
        z = src.max_zoom + 1
        _, resp, verdict = _fetch_tile(src, z, point, fetch, TAK_USER_AGENT)
        if verdict is not None and verdict.kind == "image":
            out.append(
                Finding(
                    "info",
                    f"{label}server has real tiles at z{z}, above maxZoom {src.max_zoom}",
                )
            )
    return out


def _leaves(src: AtakSource) -> list[AtakSource]:
    """Tile sources inside a (possibly nested) multi-layer source."""
    if src.kind != "multi":
        return [src]
    return [leaf for child in src.children for leaf in _leaves(child)]


def check_source(path: Path, root: Path, fetch: Fetch) -> list[Finding]:
    src = parse_source(path)
    overlay = path.relative_to(root).parts[0] == OVERLAY_DIR
    findings = _check_name(src, overlay)

    sources = _leaves(src)
    urls = " ".join(s.url or "" for s in sources)
    if any(k in urls for k in _KEY_PLACEHOLDERS):
        return findings + [Finding("info", "needs an API key; tile checks skipped")]

    bad_wms = [
        s for s in sources if s.kind == "wms" and s.tile_type not in _WMS_TILE_TYPES
    ]
    for s in bad_wms:
        findings.append(
            Finding(
                "error",
                f"WMS tileType '{s.tile_type}' is not JPG or PNG; ATAK sends format=null",
            )
        )
    if bad_wms:
        return findings

    point = _test_point(path, root)
    composite = src.kind == "multi"
    has_data: set[str] = set()
    for s in sources:
        label = f"[{s.name}] " if composite else ""
        # In a composite one layer may be transparent where another has data,
        # so emptiness is judged on the combined result below.
        findings += _check_zooms(
            s, label, point, fetch, overlay, overlay or composite, has_data
        )
    if composite and not overlay:
        for role in ("minZoom", "maxZoom"):
            if role not in has_data:
                findings.append(
                    Finding("error", f"{role}: no layer has data at the test point")
                )
    return findings


def http_fetch(
    url: str, user_agent: str, retries: int = 2, timeout: int = 20
) -> Response:
    """Real network fetch with ATAK-like behaviour (TLS verified, redirects followed)."""
    import requests

    last = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
            last = Response(
                r.status_code, r.headers.get("Content-Type"), r.content, None
            )
            if r.status_code < 500:
                return last
        except requests.RequestException as e:
            last = Response(None, None, b"", f"{type(e).__name__}: {e}")
        if attempt < retries:
            time.sleep(2 * (attempt + 1))
    assert last is not None  # the loop runs at least once
    return last


def run_harness(
    root: Path, fetch: Fetch, only: list[Path] | None = None
) -> dict[Path, list[Finding]]:
    """Check every map under root (or just ``only``); keys are paths relative to root."""
    from mapvalidator.catalog import iter_map_files

    files = [Path(f).resolve() for f in only] if only else iter_map_files(root)
    return {f.relative_to(root): check_source(f, root, fetch) for f in files}


def format_report(results: dict[Path, list[Finding]]) -> tuple[str, int]:
    """Plain-text report and process exit code (1 if any error)."""
    lines = []
    errors = 0
    for path in sorted(results, key=lambda p: p.as_posix()):
        findings = results[path]
        errors += sum(f.level == "error" for f in findings)
        mark = "FAIL" if any(f.level == "error" for f in findings) else "ok  "
        lines.append(f"{mark} {path.as_posix()}")
        lines += [f"     {f.level.upper():5} {f.message}" for f in findings]
    lines.append(f"\n{len(results)} maps, {errors} errors")
    return "\n".join(lines), 1 if errors else 0
