#!/usr/bin/env python3
"""Build the README banners (dark and light) from the brand SVGs.

Self-contained SVGs: contour art from docs/assets/brand/hero-contours-*.svg
with the outlined logo on top, so GitHub shows them without web fonts or
external files. Run after changing the logo or the contour art.
"""

import re
from pathlib import Path

BRAND = Path(__file__).resolve().parent.parent / "docs" / "assets" / "brand"
W, H = 1280, 300
LOGO_H = 92


def inner(svg: str) -> tuple[list[float], str]:
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    start, end = svg.index(">", svg.index("<svg")) + 1, svg.rindex("</svg>")
    body = svg[start:end]
    return vb, body


def banner(theme: str) -> str:
    dark = theme == "dark"
    (cx, cy, cw, ch), contours = inner(
        (BRAND / f"hero-contours-{theme}.svg").read_text()
    )
    (_, _, lw, lh), logo = inner(
        (
            BRAND / ("atak-maps-logo-dark.svg" if dark else "atak-maps-logo.svg")
        ).read_text()
    )
    logo = re.sub(r'id="([a-z]*c\d)"', rf'id="{theme}-\1"', logo)
    logo = re.sub(r"url\(#([a-z]*c\d)\)", rf"url(#{theme}-\1)", logo)
    scale = max(W / cw, H / ch)
    ls = LOGO_H / lh
    bg, line = ("#0F1B2D", "#24344A") if dark else ("#F4F6F8", "#D5DCE3")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="ATAK Maps">'
        f'<rect width="{W}" height="{H}" rx="16" fill="{bg}"/>'
        f'<clipPath id="{theme}-frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
        f'<g clip-path="url(#{theme}-frame)">'
        f'<g transform="translate({(W - cw * scale) / 2:.1f} {(H - ch * scale) / 2:.1f}) '
        f'scale({scale:.4f})">{contours}</g></g>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{line}"/>'
        f'<g transform="translate({(W - lw * ls) / 2:.1f} {(H - LOGO_H) / 2:.1f}) scale({ls:.5f})">{logo}</g>'
        "</svg>\n"
    )


if __name__ == "__main__":
    for theme in ("dark", "light"):
        out = BRAND / f"readme-banner-{theme}.svg"
        out.write_text(banner(theme))
        print(out)
