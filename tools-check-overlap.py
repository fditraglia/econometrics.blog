# /// script
# dependencies = ["playwright"]
# ///
"""Check that no two pieces of text on any page overlap, at any width.

Run against _site/ after `quarto render`:

    uv run tools-check-overlap.py            # every page
    uv run tools-check-overlap.py james      # only pages whose path matches

The two older checks each guard one symptom: tools-check-layout.py tests for
sideways scroll, tools-check-folds.py tests footnote visibility and position
around a solution fold. Neither says anything about the property a reader
actually notices, which is text drawn on top of other text. A 2026-09-05 bug
(margin notes overlapping the next paragraph everywhere between 768px and
992px, on a fresh load) passed both.

This check asserts that property directly. Every page is loaded twice: once
at the widest width and stepped down through WIDTHS, once at the narrowest
and stepped up. Each step is measured after the page's resize handlers
(the aligner in _theme.html, _math-fit.html, Quarto's layoutMarginEls) have
settled, so both fresh-load and after-resize layouts are covered at every
width. Solution folds are opened after the first measurement of each pass,
so the fold-closed state is measured once and the open state at every width.

A text block is any visible paragraph, heading, list item, code block,
figure, figure caption, table, display equation, callout header or margin
note. Two blocks overlap if their boxes intersect by more than TOLERANCE
pixels in both directions; ancestor/descendant pairs are skipped, as a note
contains its paragraph and a list item its nested list. Pages run in
parallel across WORKERS browsers; Chromium is used so that quarto.js runs
(it is a module script, which Chromium refuses to load from file://, hence
the local HTTP server).

Validated 2026-09-05 by deleting the `.column-margin.no-row-height` height
fix from the rendered stylesheet: the check then reported 157 overlapping
pairs on 25 pages, the James-Stein post among them, all between 768px and
991px, and nothing with the fix in place. It runs in about three minutes. Exits non-zero on any overlap, naming both blocks and every width at
which they collided.
"""
import functools
import http.server
import pathlib
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).parent / "_site"

# Quarto's breakpoints (768, 992), the theme's own (900), the phone widths
# the layout check uses, and a few in between. Each breakpoint is tested on
# both sides.
WIDTHS = (360, 390, 480, 600, 700, 767, 768, 830, 899, 900, 991, 992,
          1100, 1200, 1440)
TOLERANCE = 3     # px of intersection in both directions before it counts
SETTLE_MS = 450   # aligner and _math-fit debounce 150ms; Quarto throttles 50ms
WORKERS = 4


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve_site():
    handler = functools.partial(QuietHandler, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


PROBE = r"""(tolerance) => {
  const root = document.getElementById('quarto-content') || document.body;
  const sel = 'p, h1, h2, h3, h4, h5, h6, li, pre, figure, figcaption, table, ' +
              'img, svg, mjx-container[display="true"], .callout-header, ' +
              '.column-margin > div[id^="fn"]';
  const blocks = [];
  root.querySelectorAll(sel).forEach(el => {
    if (!el.offsetParent && getComputedStyle(el).position !== 'fixed') return;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;
    if (!el.textContent.trim() && !/^(IMG|SVG|FIGURE)$/.test(el.tagName)) return;
    // An inline element that wraps (the "On this page" list at the top of
    // a post) has a bounding box covering both lines, which would read as
    // overlapping its neighbors. Use its per-line boxes instead.
    const inline = getComputedStyle(el).display === 'inline';
    const rects = inline ? [...el.getClientRects()] : [r];
    blocks.push({el, top: r.top, bottom: r.bottom, left: r.left, right: r.right, rects});
  });
  blocks.sort((a, b) => a.top - b.top);
  const label = el => {
    const tag = el.tagName.toLowerCase();
    const id = el.id ? '#' + el.id : '';
    const cls = el.classList.length ? '.' + [...el.classList].slice(0, 2).join('.') : '';
    const text = el.textContent.trim().replace(/\s+/g, ' ').slice(0, 50);
    return tag + id + cls + (text ? ' "' + text + '"' : '');
  };
  const out = [];
  for (let i = 0; i < blocks.length; i++) {
    const a = blocks[i];
    for (let j = i + 1; j < blocks.length; j++) {
      const b = blocks[j];
      if (b.top >= a.bottom - tolerance) break;  // sorted by top: nothing later can overlap a
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      let dx = 0, dy = 0;
      for (const ra of a.rects) for (const rb of b.rects) {
        const y = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
        const x = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
        if (y > tolerance && x > tolerance) { dx = Math.max(dx, x); dy = Math.max(dy, y); }
      }
      if (!dx) continue;
      out.push({a: label(a.el), b: label(b.el), dx: Math.round(dx), dy: Math.round(dy)});
    }
  }
  return out;
}"""


def pages():
    index = SITE / "index.html"
    if not index.exists():
        sys.exit("No _site/ found. Run `quarto render` first.")
    yield index
    yield from sorted(SITE.glob("post/*/index.html"))
    for page in ("about", "subscribe"):
        path = SITE / page / "index.html"
        if path.exists():
            yield path
    for path in sorted(SITE.glob("*.html")):
        if path.name != "index.html":
            yield path


def check_pages(paths, port):
    """Run one browser over a batch of pages; return {(page, a, b): [widths]}."""
    found = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        for path in paths:
            rel = path.relative_to(SITE).as_posix()
            url = f"http://127.0.0.1:{port}/{rel}"
            name = rel.removesuffix("/index.html").removesuffix(".html")
            for widths in (tuple(reversed(WIDTHS)), WIDTHS):
                page.set_viewport_size({"width": widths[0], "height": 900})
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(SETTLE_MS)
                for k, width in enumerate(widths):
                    if k:
                        page.set_viewport_size({"width": width, "height": 900})
                        page.wait_for_timeout(SETTLE_MS)
                    for hit in page.evaluate(PROBE, TOLERANCE):
                        key = (name, hit["a"], hit["b"])
                        found.setdefault(key, []).append(width)
                    if k == 0:
                        # Fold-closed state measured once; open for the rest.
                        headers = page.query_selector_all(
                            ".callout.solution .callout-header.collapsed")
                        for h in headers:
                            h.click()
                        if headers:
                            page.wait_for_timeout(700)  # collapse animation
        browser.close()
    return found


def main():
    targets = list(pages())
    wanted = sys.argv[1:]
    if wanted:
        targets = [p for p in targets if any(w in str(p) for w in wanted)]
        print(f"Checking {len(targets)} of the site's pages ({' '.join(wanted)}).")
    server = serve_site()
    port = server.server_address[1]
    batches = [targets[i::WORKERS] for i in range(WORKERS)]
    found = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for part in pool.map(lambda b: check_pages(b, port), batches):
            found.update(part)
    server.shutdown()

    for (name, a, b), widths in sorted(found.items()):
        ws = sorted(set(widths))
        print(f"{name} at {', '.join(map(str, ws))}px:")
        print(f"    {a}")
        print(f"    {b}")
    print(f"\n{len(found)} overlapping pair(s) across {len(targets)} pages "
          f"at {len(WIDTHS)} widths.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
