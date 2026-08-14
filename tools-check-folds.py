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

Notes are matched as li[id^="fn"] and div[id^="fn"]: pandoc renders end-of-
section notes as list items and margin notes as divs. An early version
looked only at list items and reported a leaking page as clean.

Exits non-zero on any violation, naming the note and which way it went.
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).parent / "_site"

PROBE = """() => {
  const fold = document.querySelector('.callout.solution');
  if (!fold) return null;
  const visible = el => !!(el && el.offsetParent !== null);
  const out = [];
  document.querySelectorAll('li[id^="fn"], div[id^="fn"]').forEach(note => {
    if (/^fnref/.test(note.id)) return;  // a marker, not a note
    const marker = document.querySelector('a[href="#' + note.id + '"]');
    out.push({
      id: note.id,
      noteVisible: visible(note),
      markerVisible: marker ? visible(marker) : null,
      text: note.textContent.trim().slice(0, 60),
    });
  });
  return out;
}"""


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
    folds, failures = 0, []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        for path in pages:
            page.goto(path.as_uri(), wait_until="networkidle")
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
        browser.close()

    for path, note, problem in failures:
        print(f"{path.parent.name}: {note['id']} {problem}")
        print(f"    {note['text']}...")

    print(f"{len(failures)} violation(s) across {folds} page(s) with a fold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
