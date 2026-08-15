#!/usr/bin/env python3
"""Rewrite relative links in the generated RSS feeds to absolute URLs.

Quarto makes image sources absolute when it builds a feed, and it strips
same-page anchors (`href="#section"`) because they point nowhere once an item
is republished. It does neither for links to other posts, which stay in the
page-relative form Quarto emits, e.g. `../../post/some-slug/`.

A browser resolves a relative link against the address of the page showing it.
On this site that lands correctly. When an aggregator such as R-bloggers
republishes a feed item at its own URL, the same link resolves against *their*
address and 404s. Roughly a third of the posts here link to a previous post,
so this is worth correcting.

Quarto has no setting for it (the internal switch is called `urls-to-absolute`
but only ever queries `img`), and a Lua filter cannot reach it: the feed's
content is assembled after rendering, by re-reading the finished HTML. A
post-render script is the only layer where the fix applies, so this runs from
`project: post-render` in `_quarto.yml`.

Each link is resolved against its own item's `<link>`, which is the absolute
URL of that post -- exactly the base a browser would have used on this site.
Absolute URLs are left alone, so re-running this is harmless.

No third-party packages: this runs in CI, where only the standard library and
Quarto itself are available.
"""

import os
import pathlib
import re
import sys
from urllib.parse import urljoin

OUTPUT_DIR = pathlib.Path(
    os.environ.get("QUARTO_PROJECT_OUTPUT_DIR")
    or pathlib.Path(__file__).resolve().parent / "_site"
)

# Left as written: already absolute, protocol-relative, or not a location.
LEAVE_ALONE = ("http://", "https://", "//", "mailto:", "data:", "#")

ITEM = re.compile(r"<item>.*?</item>", re.S)
ITEM_LINK = re.compile(r"<link>(.*?)</link>", re.S)
LOCATION_ATTR = re.compile(r'\b(href|src)="([^"]*)"')


def absolutize_item(item: str) -> tuple[str, int]:
    """Resolve every relative href/src in one feed item against its own link."""
    link = ITEM_LINK.search(item)
    if not link:
        return item, 0
    base = link.group(1).strip()
    if not base.startswith(("http://", "https://")):
        # Without an absolute base there is nothing to resolve against.
        return item, 0

    count = 0

    def replace(match: re.Match) -> str:
        nonlocal count
        attr, url = match.group(1), match.group(2)
        if not url or url.startswith(LEAVE_ALONE):
            return match.group(0)
        count += 1
        return f'{attr}="{urljoin(base, url)}"'

    return LOCATION_ATTR.sub(replace, item), count


def absolutize_feed(path: pathlib.Path) -> int:
    text = path.read_text(encoding="utf-8")
    if "<rss" not in text:
        return 0

    total = 0
    items_touched = 0

    def replace(match: re.Match) -> str:
        nonlocal total, items_touched
        rewritten, count = absolutize_item(match.group(0))
        if count:
            total += count
            items_touched += 1
        return rewritten

    rewritten = ITEM.sub(replace, text)
    if total:
        path.write_text(rewritten, encoding="utf-8")
        print(
            f"[feed-links] {path.name}: {total} relative link(s) "
            f"made absolute across {items_touched} item(s)"
        )
    return total


def main() -> int:
    if not OUTPUT_DIR.is_dir():
        # Nothing rendered yet; not an error worth failing a build over.
        return 0
    for path in sorted(OUTPUT_DIR.rglob("*.xml")):
        absolutize_feed(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
