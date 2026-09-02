# /// script
# dependencies = ["playwright"]
# ///
"""Check that no solution fold leaks a footnote, in either direction.

Run against _site/ after `quarto render`:

    uv run tools-check-folds.py

A puzzler post hides its solution behind a collapsed callout. Its footnotes
are ordinary margin footnotes, and Quarto hoists margin notes out of the
fold's collapse container so the page grid can place them -- left alone, a
note cited inside a closed fold would sit readable in the margin beside it,
giving the answer away. A rule in custom.scss therefore hides every margin
note that follows a collapsed fold (a fold always runs to the end of its
post, so those notes all belong to the solution) and reveals them when the
fold opens.

The invariant this enforces is about what a reader can see, not where the
markup sits: at any moment, a note must be readable exactly when its marker
is readable. Both failure directions matter -- a readable note with a hidden
marker leaks the solution, and a visible marker with a hidden note points at
nothing. The check runs twice per page, once with the fold shut and once
after opening it.

A third pass guards note POSITION, not just visibility. Three scripts touch
where a margin note sits: Quarto's layoutMarginEls (re-runs on any body-
height change), the aligner in _theme.html (marker-ordered, the one that
must win), and _math-fit.html (rescales equations, moving every marker
below them). A 2026-09-01 bug scattered a fold's notes after any window
resize -- fresh loads were always clean, so no static check could see it.
With the fold open, this pass resizes the viewport 1440 -> 1000 -> 1440
(crossing the width where _math-fit rescales and Quarto's pass fires) and
then asserts the aligner's contract: notes in marker order, each level with
its marker or 14px below the previous note, within 2px.

Notes are matched as li[id^="fn"] and div[id^="fn"]: pandoc renders end-of-
section notes as list items and margin notes as divs. An early version
looked only at list items and reported a leaking page as clean.

Exits non-zero on any violation, naming the note and which way it went.
"""
import functools
import http.server
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).parent / "_site"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve_site():
    """Serve _site/ over local HTTP on an ephemeral port.

    Chromium refuses to load quarto.js from a file:// page (it is a module
    script, blocked by CORS), so under file:// Quarto's layoutMarginEls
    never runs -- the very actor the alignment pass exists to guard against.
    The visibility passes don't care, but the check must exercise the page
    with all of its scripts, as production does.
    """
    handler = functools.partial(QuietHandler, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server

PROBE = """() => {
  const fold = document.querySelector('.callout.solution');
  if (!fold) return null;
  const visible = el => !!(el && el.offsetParent !== null);
  const out = [];
  document.querySelectorAll('li[id^="fn"], div[id^="fn"]').forEach(note => {
    if (/^fnref/.test(note.id)) return;  // a marker, not a note
    // Look the marker up by id: quarto.js rewrites footnote hrefs from
    // "#fn1" to absolute URLs at runtime, so matching on href breaks once
    // the page's scripts have run. href$= is kept as a fallback.
    const marker = document.getElementById('fnref' + note.id.slice(2)) ||
                   document.querySelector('a[href$="#' + note.id + '"]');
    out.push({
      id: note.id,
      noteVisible: visible(note),
      markerVisible: marker ? visible(marker) : null,
      text: note.textContent.trim().slice(0, 60),
    });
  });
  return out;
}"""

# Mirrors the aligner in _theme.html: pair each margin note with its marker,
# skip notes folded into the body flow (narrow screens), sort by marker
# position, and compute the target the aligner should have set -- level with
# the marker, or 14px below the previous note, whichever is lower.
ALIGN_PROBE = r"""() => {
  const main = document.querySelector('main');
  const textLeft = main.getBoundingClientRect().left;
  const textWidth = (document.querySelector('main p') || main).clientWidth;
  const pairs = [];
  document.querySelectorAll('.column-margin div[id^="fn"]').forEach(note => {
    const m = note.id.match(/^fn(\d+)$/);
    const marker = m && document.getElementById('fnref' + m[1]);
    if (!marker || !note.offsetParent || !marker.offsetParent) return;
    const nr = note.getBoundingClientRect();
    if (nr.left < textLeft + textWidth * 0.8) return;  // note is in body flow
    pairs.push({
      id: note.id,
      text: note.textContent.trim().slice(0, 60),
      noteTop: nr.top + window.scrollY,
      height: nr.height,
      markerTop: marker.getBoundingClientRect().top + window.scrollY,
    });
  });
  pairs.sort((a, b) => a.markerTop - b.markerTop);
  const out = [];
  let lastBottom = -Infinity;
  for (const p of pairs) {
    const expected = Math.max(p.markerTop, lastBottom + 14);
    out.push({id: p.id, text: p.text,
              expected: Math.round(expected), actual: Math.round(p.noteTop)});
    lastBottom = expected + p.height;
  }
  return out;
}"""

ALIGN_TOLERANCE = 2  # px


def collect(notes, state, failures, path):
    for n in notes:
        if n["markerVisible"] is None:
            failures.append((path, n, "has no marker anywhere on the page"))
        elif n["noteVisible"] and not n["markerVisible"]:
            failures.append(
                (path, n, f"is readable while its marker is hidden ({state}) -- leaks the solution"))
        elif n["markerVisible"] and not n["noteVisible"]:
            failures.append(
                (path, n, f"is hidden while its marker is in plain view ({state})"))


def main():
    index = SITE / "index.html"
    if not index.exists():
        sys.exit("No _site/ found. Run `quarto render` first.")

    pages = sorted(SITE.glob("post/*/index.html"))
    server = serve_site()
    port = server.server_address[1]
    folds, failures = 0, []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for path in pages:
            page.goto(f"http://127.0.0.1:{port}/post/{path.parent.name}/",
                      wait_until="networkidle")
            page.wait_for_timeout(500)
            notes = page.evaluate(PROBE)
            if notes is None:
                continue
            folds += 1
            collect(notes, "fold closed", failures, path)
            # Open every fold on the page and re-check.
            for header in page.query_selector_all(".callout.solution .callout-header"):
                header.click()
            page.wait_for_timeout(700)  # Bootstrap collapse animation
            collect(page.evaluate(PROBE), "fold open", failures, path)
            # Resize round-trip, then check the notes still sit where the
            # aligner's contract says. 800ms per step lets the debounced
            # resize handlers (aligner, _math-fit, Quarto) all finish.
            for width in (1000, 1440):
                page.set_viewport_size({"width": width, "height": 900})
                page.wait_for_timeout(800)
            for row in page.evaluate(ALIGN_PROBE):
                if abs(row["expected"] - row["actual"]) > ALIGN_TOLERANCE:
                    failures.append((path, row,
                        f"sits at {row['actual']}px, expected {row['expected']}px "
                        "(after resize round-trip) -- the aligner lost to a later layout pass"))
        browser.close()
    server.shutdown()

    for path, note, problem in failures:
        print(f"{path.parent.name}: {note['id']} {problem}")
        print(f"    {note['text']}...")

    print(f"{len(failures)} violation(s) across {folds} page(s) with a fold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
