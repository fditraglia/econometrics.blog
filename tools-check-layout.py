# /// script
# dependencies = ["playwright"]
# ///
"""Check that no rendered page scrolls sideways at any reading width.

Run against _site/ after `quarto render`:

    uv run tools-check-layout.py

The browsers this needs are not installed by uv. Once per machine:

    uv run --with playwright playwright install chromium webkit

Horizontal scroll is measured by actually scrolling the page and reading back
window.scrollX, not by comparing scrollWidth to clientWidth. The latter reports
an overflow for content sitting inside a container that scrolls on its own,
which is correct behavior rather than a fault.

Exits non-zero when any page scrolls, and names the widest element that is not
inside a scrolling container, which is usually the cause.
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).parent / "_site"

# 390 is a common phone; 768 is where Quarto would reveal the table of contents;
# 900 is where this site does reveal it, and where the page grid is still wider
# than the screen for a post using `column: page`; 1200 is a laptop.
WIDTHS = (390, 768, 900, 1200)

PROBE = """() => {
  window.scrollTo(500, 0);
  const moved = Math.round(window.scrollX);
  window.scrollTo(0, 0);
  if (!moved) return {moved: 0};
  const w = document.documentElement.clientWidth;
  const name = e => {
    const cls = (typeof e.className === 'string' && e.className)
      ? '.' + e.className.trim().split(/\\s+/).slice(0, 2).join('.') : '';
    return e.tagName + cls;
  };
  let outside = null, widest = null;
  document.querySelectorAll('body *').forEach(e => {
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.right <= w + 1) return;
    if (!widest || r.right > widest.right)
      widest = {tag: name(e), right: Math.round(r.right)};
    // A child of a scrolling box may legitimately extend past the viewport, so
    // the likeliest cause is the widest element that is not inside one.
    let p = e.parentElement;
    while (p && p !== document.body) {
      if (/auto|scroll/.test(getComputedStyle(p).overflowX)) return;
      p = p.parentElement;
    }
    if (!outside || r.right > outside.right)
      outside = {tag: name(e), right: Math.round(r.right)};
  });
  return {moved, worst: outside, widest};
}"""


def pages():
    index = SITE / "index.html"
    if not index.exists():
        sys.exit("No _site/ found. Run `quarto render` first.")
    yield index
    yield from sorted(SITE.glob("post/*/index.html"))
    about = SITE / "about" / "index.html"
    if about.exists():
        yield about
    # Unlisted, but it renders a table and tables are what overflow narrow
    # screens; nothing else would catch it.
    r_feed = SITE / "r-feed.html"
    if r_feed.exists():
        yield r_feed


def main():
    targets = list(pages())
    failures = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for width in WIDTHS:
            page = browser.new_page(viewport={"width": width, "height": 900})
            for path in targets:
                page.goto(path.as_uri(), wait_until="networkidle")
                page.wait_for_timeout(1500)  # MathJax typesets after load
                result = page.evaluate(PROBE)
                if result["moved"]:
                    failures.append((width, path, result))
            page.close()
        browser.close()

    for width, path, result in failures:
        name = path.parent.name if path.parent.name != "_site" else "index"
        worst = result.get("worst") or result.get("widest")
        if worst:
            inside = " (inside a scrolling box)" if not result.get("worst") else ""
            cause = f"{worst['tag']} extends to {worst['right']}px{inside}"
        else:
            cause = "no overflowing element; suspect a pseudo-element or a transform"
        print(f"{width}px  scrolls {result['moved']}px  {name}  ({cause})")

    print(f"\n{len(failures)} failure(s) across {len(targets)} pages at {len(WIDTHS)} widths.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
