# /// script
# dependencies = ["playwright"]
# ///
"""Check that no solution fold hides a footnote whose marker is in plain view.

Run against _site/ after `quarto render`:

    uv run tools-check-folds.py

A puzzler post hides its solution behind a collapsed callout. Quarto prints
footnotes at the foot of the page by default, so a note cited inside a fold
would be readable without opening it, which gives the answer away. The posts
therefore set `reference-location: section`, which prints each note at the end
of the section that cites it.

That placement is only correct when the fold has a section to itself. A section
that begins before the fold ends inside it, so its notes are carried inside too
-- leaving a marker in the visible text pointing at hidden content, which is
the opposite failure and just as broken. A `## Solution` heading immediately
above the fold is what prevents it.

Neither `quarto render` nor tools-check-layout.py can see either fault, hence
this check: for every footnote on a page with a fold, the marker and the note
must be on the same side of it.

Exits non-zero when they are not, naming the note and which way it went.
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).parent / "_site"

PROBE = """() => {
  const fold = document.querySelector('.callout.solution');
  if (!fold) return null;
  const out = [];
  document.querySelectorAll('li[id^="fn"]').forEach(note => {
    const marker = document.querySelector('a[href="#' + note.id + '"]');
    out.push({
      id: note.id,
      noteInside: fold.contains(note),
      markerInside: marker ? fold.contains(marker) : null,
      text: note.textContent.trim().slice(0, 60),
    });
  });
  return out;
}"""


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
            for n in notes:
                if n["markerInside"] is None:
                    failures.append((path, n, "has no marker anywhere on the page"))
                elif n["markerInside"] and not n["noteInside"]:
                    failures.append((path, n, "is cited inside the fold but printed outside it"))
                elif n["noteInside"] and not n["markerInside"]:
                    failures.append((path, n, "is cited outside the fold but printed inside it"))
        browser.close()

    for path, note, problem in failures:
        print(f"{path.parent.name}: {note['id']} {problem}")
        print(f"    {note['text']}...")

    print(f"{len(failures)} misplaced note(s) across {folds} page(s) with a fold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
