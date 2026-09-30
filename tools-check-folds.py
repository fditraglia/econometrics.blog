# /// script
# dependencies = ["playwright==1.63.0"]
# ///
"""Check solution visibility, keyboard controls and note reading order.

Run after `quarto render`: uv run tools-check-folds.py
Fresh desktop/mobile/tablet loads, independent folds, Space/Enter activation,
closing and reopening, and resizing in both directions are covered. Notes must
follow reference order in the DOM and visually; margin notes must also align.
"""
import functools
import http.server
import pathlib
import re
import runpy
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

# Geometry contract, independent of the aligner's CSS mode flag.
ALIGN_PROBE = r"""() => {
  const main = document.querySelector('main');
  const textLeft = main.getBoundingClientRect().left;
  // The first *visible* paragraph: one inside a closed fold has zero width.
  const para = [...main.querySelectorAll('p')].find(p => p.offsetParent);
  const textWidth = (para || main).clientWidth;
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


ORDER_PROBE = r"""() => {
  const markers = [...document.querySelectorAll('a.footnote-ref')];
  const visible = el => el && el.getClientRects().length > 0;
  const notes = [...document.querySelectorAll('.column-margin div[id^="fn"]')]
    .filter(visible);
  const rank = note => markers.findIndex(m =>
    m.href.split('#').pop() === note.id && visible(m));
  const errors = [];
  for (let i = 1; i < notes.length; i++) {
    if (rank(notes[i]) < rank(notes[i-1])) errors.push('DOM order: ' + notes[i-1].id + ', ' + notes[i].id);
    if (notes[i].getBoundingClientRect().top < notes[i-1].getBoundingClientRect().bottom - 2)
      errors.push('visual order/overlap: ' + notes[i-1].id + ', ' + notes[i].id);
  }
  return errors;
}"""


def main():
    if not (SITE / "index.html").exists():
        sys.exit("No _site/ found. Run `quarto render` first.")
    pages = [p for p in sorted(SITE.glob("post/*/index.html"))
             if re.search(r'<div[^>]+class="[^"]*\bsolution\b', p.read_text())]
    server = serve_site()
    port = server.server_address[1]
    failures = []

    def check(page, path, state):
        collect(page.evaluate(PROBE), state, failures, path)
        for error in page.evaluate(ORDER_PROBE):
            failures.append((path, {"id": "order", "text": state}, error))
        for row in page.evaluate(ALIGN_PROBE):
            if abs(row["expected"] - row["actual"]) > ALIGN_TOLERANCE:
                failures.append((path, row, f"{state}: at {row['actual']}px, expected {row['expected']}px"))
        overflow = page.evaluate("() => {window.scrollTo(500, window.scrollY); const x = window.scrollX; window.scrollTo(0, window.scrollY); return x;}")
        if overflow:
            failures.append((path, {"id": "overflow", "text": state}, f"scrolls sideways {overflow}px"))

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for path in pages:
            url = f"http://127.0.0.1:{port}/post/{path.parent.name}/"
            for width in (390, 830, 991, 992, 1023, 1024, 1440):
                page.set_viewport_size({"width": width, "height": 900})
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(500)
                check(page, path, f"{width}px closed")
                headers = page.locator('.callout.solution .callout-header')
                for i in range(headers.count()):
                    header = headers.nth(i)
                    if header.evaluate("el => el.tagName !== 'BUTTON' || el.type !== 'button'"):
                        failures.append((path, {"id": "toggle", "text": ""}, "not a native button"))
                    header.focus()
                    page.keyboard.press('Shift+Tab')
                    page.keyboard.press('Tab')
                    if not header.evaluate('el => el === document.activeElement'):
                        failures.append((path, {"id": "toggle", "text": ""}, "not in keyboard tab order"))
                    header.press('Space')
                    page.wait_for_timeout(700)
                    if header.get_attribute('aria-expanded') != 'true':
                        failures.append((path, {"id": "toggle", "text": ""}, "Space did not open solution"))
                    check(page, path, f"{width}px fold {i+1} opened with Space")
                    header.press('Enter')
                    page.wait_for_timeout(700)
                    if header.get_attribute('aria-expanded') != 'false':
                        failures.append((path, {"id": "toggle", "text": ""}, "Enter did not close solution"))
                    check(page, path, f"{width}px fold {i+1} closed with Enter")
                    header.click()
                    page.wait_for_timeout(700)
                check(page, path, f"{width}px all open")
            for width in (992, 830, 390, 830, 992, 1440):
                page.set_viewport_size({"width": width, "height": 900})
                page.wait_for_timeout(800)
                check(page, path, f"resized to {width}px")
            print(f"Checked {path.parent.name}", flush=True)

        # Exercise the old ownership failure even though today's articles
        # happen to end with their only solution. Serve a synthetic body in
        # a real rendered page so it uses the actual CSS and Bootstrap JS.
        fixture = runpy.run_path(str(SITE.parent / 'tests/test_normalize_notes.py'))
        marker, note, margin, fold = (fixture[k] for k in ('marker', 'note', 'margin', 'fold'))
        body = (fold('<p>First solution' + marker(1) + '</p>') + margin(note(1)) +
                fold('<p>Second solution' + marker(2) + '</p>', 2) + margin(note(2)) +
                '<p>Ordinary content after both solutions' + marker(3) + '</p>' + margin(note(3)))
        source = pages[0].read_text()
        source = re.sub(r'(<main\b[^>]*>).*?(</main>)',
                        lambda m: m[1] + body + m[2], source, flags=re.S)
        source = fixture['normalize'](source)
        url = f"http://127.0.0.1:{port}/post/{pages[0].parent.name}/?notes-fixture"
        page.route(url, lambda route: route.fulfill(body=source, content_type='text/html'))
        for width in (390, 1440):
            page.set_viewport_size({'width': width, 'height': 900})
            page.goto(url, wait_until='networkidle')
            check(page, pages[0], f'fixture {width}px both closed')
            headers = page.locator('.callout.solution .callout-header')
            for i in (0, 1, 0, 1):
                headers.nth(i).press('Enter')
                page.wait_for_timeout(700)
                check(page, pages[0], f'fixture {width}px toggled fold {i+1}')

        # Mutation check: prove the reading-order assertion catches the
        # original reversal, rather than merely reporting the fixed site green.
        for header in page.locator('.callout.solution .callout-header').all():
            header.click()
        page.set_viewport_size({'width': 390, 'height': 900})
        page.wait_for_timeout(700)
        page.evaluate("""() => {
          const notes = [...document.querySelectorAll('[data-note-refs]')];
          const holder = notes[0].parentElement;
          notes.reverse().forEach(n => holder.appendChild(n));
        }""")
        if not page.evaluate(ORDER_PROBE):
            failures.append((pages[0], {'id': 'mutation', 'text': ''},
                             'order check failed to detect deliberately reversed notes'))
        # Initial HTML must already hide solution notes, before JS runs.
        context = browser.new_context(java_script_enabled=False,
                                      viewport={"width": 390, "height": 900})
        static_page = context.new_page()
        for path in pages:
            static_page.goto(f"http://127.0.0.1:{port}/post/{path.parent.name}/",
                             wait_until="networkidle")
            collect(static_page.evaluate(PROBE), "JavaScript disabled", failures, path)
        browser.close()
    server.shutdown()
    for path, note, problem in failures:
        print(f"{path.parent.name}: {note['id']} {problem} {note['text']}")
    print(f"{len(failures)} violation(s) across {len(pages)} page(s) with a fold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
