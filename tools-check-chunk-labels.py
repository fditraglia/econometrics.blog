# /// script
# requires-python = ">=3.11"
# ///
"""Catch code appendices that silently render as nothing.

Several posts show a figure without its code, then repeat the code further
down in an appendix. The knitr idiom for that is to run the real chunk with
`echo: false` and then write an *empty* chunk carrying the *same label* plus
`eval: false`; knitr copies the earlier chunk's source into the empty one and
prints it without re-running it.

If the two labels do not match, there is nothing to copy. The empty chunk
renders as nothing at all, knitr reports no error, and the post is left saying
"the R code is as follows:" above blank space. That has happened five times
here, in four posts, and went unnoticed for years -- a rendered post looks
fine unless you read the sentence before the gap.

This flags any empty chunk whose label matches no earlier chunk in the same
file, and suggests the near miss. Runs in well under a second; no third-party
packages.

    uv run tools-check-chunk-labels.py
"""

import pathlib
import re
import sys

POSTS = pathlib.Path(__file__).resolve().parent / "post"
CHUNK = re.compile(r"^```\{r\}\n(.*?)^```$", re.S | re.M)
LABEL = re.compile(r"#\|\s*label:\s*(\S+)")


def problems(path: pathlib.Path) -> list[tuple[str, list[str]]]:
    text = path.read_text(encoding="utf-8")
    defined: list[str] = []
    empty: list[str] = []

    for body in CHUNK.findall(text):
        options = [ln for ln in body.splitlines() if ln.lstrip().startswith("#|")]
        code = [
            ln
            for ln in body.splitlines()
            if not ln.lstrip().startswith("#|") and ln.strip()
        ]
        label = None
        for option in options:
            found = LABEL.match(option.strip())
            if found:
                label = found.group(1)
        if code:
            if label:
                defined.append(label)
        elif label:
            empty.append(label)

    found = []
    for label in empty:
        if label not in defined:
            near = [d for d in defined if d in label or label in d]
            found.append((label, near))
    return found


def main() -> int:
    failures = 0
    for path in sorted(POSTS.glob("*/index.qmd")):
        for label, near in problems(path):
            failures += 1
            print(f"{path.parent.name}")
            print(f'    empty chunk labeled "{label}" matches no earlier chunk')
            if near:
                print(f'    did you mean "{near[0]}"?')
    if failures:
        print(f"\n{failures} appendix chunk(s) will render as nothing.")
        return 1
    print(f"No orphaned chunk labels in {len(list(POSTS.glob('*/index.qmd')))} posts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
