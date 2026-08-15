# /// script
# dependencies = ["fonttools", "brotli", "playwright", "pillow"]
# ///
"""Regenerate the site icons from the mark's two ingredients: a Libre Caslon
Text Bold 'e' and a vermilion dot.

The original icons were raster only, at 64px and 180px, which is too small for
anything that wants a larger square -- Buttondown's newsletter icon asks for
300x300, and upscaling the 64px favicon to that is what prompted this. Drawing
the mark from the font instead means any size is exact.

Geometry is measured from the original apple-touch-icon.png and expressed as
fractions of the canvas, so the proportions of the hand-made original are
preserved rather than re-invented. The glyph is Libre Caslon Text *Bold*: its
'e' has an aspect ratio of 0.978 against the original's 0.976, where the
regular weight is 0.858.

Outputs, all committed:
  icon.svg      vector master, also served as the SVG favicon (dark-mode aware)
  favicon.png   64x64, the fallback favicon for browsers that ignore SVG
  apple-touch-icon.png  180x180
  icon-300.png  300x300, for uploading to Buttondown

Run with `uv run tools-make-icons.py`. Needs the chromium that
tools-check-layout.py already relies on for rasterizing.
"""

import pathlib

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

REPO = pathlib.Path(__file__).resolve().parent

# Matching custom.scss: $paper, $ink-strong, $vermilion.
PAPER = "#f8f6f1"
INK = "#14120f"
VERMILION = "#a63a1c"

# Measured from the original 180x180 apple-touch-icon.png, as fractions of the
# canvas. The 'e' and the dot share a baseline.
E_LEFT, E_TOP, E_W, E_H = 29 / 180, 51 / 180, 81 / 180, 83 / 180
DOT_CX, DOT_CY, DOT_R = 135 / 180, 120.5 / 180, 13.5 / 180

FONT = REPO / "fonts" / "libre-caslon-text-latin-700-normal.woff2"


def glyph_path_and_bounds() -> tuple[str, tuple[float, float, float, float]]:
    font = TTFont(FONT)
    glyph_set = font.getGlyphSet()
    name = font.getBestCmap()[ord("e")]
    pen = SVGPathPen(glyph_set)
    glyph_set[name].draw(pen)
    bounds_pen = BoundsPen(glyph_set)
    glyph_set[name].draw(bounds_pen)
    return pen.getCommands(), bounds_pen.bounds


PATH, (X_MIN, Y_MIN, X_MAX, Y_MAX) = glyph_path_and_bounds()
GLYPH_W = X_MAX - X_MIN
GLYPH_H = Y_MAX - Y_MIN


def svg(size: int, dark_aware: bool = False) -> str:
    """The mark on a square canvas.

    dark_aware adds a prefers-color-scheme rule so the favicon does not sit in
    a dark browser tab as a bright cream square. The dot keeps its color in
    both schemes; vermilion carries enough contrast either way.
    """
    # Land the glyph's bounding box exactly on the measured box. SVG's y axis
    # points down and the font's points up, hence the negative y scale.
    sx = (E_W * size) / GLYPH_W
    sy = (E_H * size) / GLYPH_H
    tx = E_LEFT * size - X_MIN * sx
    ty = E_TOP * size + Y_MAX * sy

    style = ""
    if dark_aware:
        style = (
            "  <style>\n"
            "    @media (prefers-color-scheme: dark) {\n"
            f"      .paper {{ fill: {INK}; }}\n"
            f"      .ink {{ fill: {PAPER}; }}\n"
            "    }\n"
            "  </style>\n"
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}">\n'
        f"{style}"
        f'  <rect class="paper" width="{size}" height="{size}" fill="{PAPER}"/>\n'
        f'  <path class="ink" d="{PATH}" fill="{INK}"'
        f' transform="translate({tx:.3f} {ty:.3f}) scale({sx:.6f} {-sy:.6f})"/>\n'
        f'  <circle cx="{DOT_CX * size:.3f}" cy="{DOT_CY * size:.3f}"'
        f' r="{DOT_R * size:.3f}" fill="{VERMILION}"/>\n'
        "</svg>\n"
    )


def rasterize(svg_text: str, out: pathlib.Path, size: int) -> None:
    from playwright.sync_api import sync_playwright

    tmp = out.with_suffix(".tmp.svg")
    tmp.write_text(svg_text, encoding="utf-8")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": size, "height": size})
            page.goto(tmp.as_uri())
            page.screenshot(path=str(out))
            browser.close()
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    (REPO / "icon.svg").write_text(svg(180, dark_aware=True), encoding="utf-8")
    print("icon.svg")
    for name, size in (
        ("favicon.png", 64),
        ("apple-touch-icon.png", 180),
        ("icon-300.png", 300),
    ):
        rasterize(svg(size), REPO / name, size)
        print(f"{name} ({size}x{size})")


if __name__ == "__main__":
    main()
