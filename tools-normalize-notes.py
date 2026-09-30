#!/usr/bin/env python3
"""Normalize Quarto's HTML after rendering, before it is published.

Runs as a `post-render` step in _quarto.yml, over every page in _site/. It
does three things:

1. Puts margin notes in reference order. Quarto hoists notes cited inside a
   collapsed callout out of the collapse container and writes them in reverse
   (puzzler 1 came out 1, 2, 3, 6, 5, 4). On wide screens the aligner used to
   hide this with offsets, but below the margin breakpoint notes fall into the
   text in HTML order, so phone readers saw them reversed. Only runs of
   adjacent note containers are sorted, never across body text, captions or
   asides. The reversal happens in Quarto's own final HTML pass, which no Lua
   filter reaches, hence a post-render step.
2. Stamps each note with data-note-refs, the IDs of the markers that cite it,
   and marks `hidden` any note whose markers are all inside closed folds.
   _notes.html keeps visibility in step from there. Explicit references replace
   the old CSS rule that hid every note after a closed fold, which required a
   fold to run to the end of its post.
3. Turns each solution fold's header, a clickable div in Quarto's output, into
   a native <button> with real "Click to reveal" / "Hide" text, so it is in
   the keyboard tab order and works with Space and Enter.

Only the tags it changes are re-serialized; everything else, including math,
scripts and whitespace, is written back verbatim, and a second run changes
nothing. Markup it does not understand stops the render with an error rather
than being passed through half-transformed. Standard library only, so CI needs
nothing installed. tests/test_normalize_notes.py covers it.
"""
from dataclasses import dataclass, field
from html import escape
from html.parser import HTMLParser
import os
from pathlib import Path
import re


VOID = set("area base br col embed hr img input link meta param source track wbr".split())


@dataclass(eq=False)
class Element:
    tag: str
    attrs: dict
    start: str
    parent: object = None
    children: list = field(default_factory=list)
    end: str = ""

    def has(self, cls):
        return cls in self.attrs.get("class", "").split()

    def set(self, key, value):
        self.attrs[key] = value
        self.start = "<" + self.tag + "".join(
            " " + k + (f'="{escape(v, quote=True)}"' if v is not None else "")
            for k, v in self.attrs.items()) + ">"

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Element):
                yield from child.walk()

    def html(self):
        return self.start + "".join(
            c.html() if isinstance(c, Element) else c for c in self.children
        ) + self.end


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.root = Element("", {}, "")
        self.stack = [self.root]
        self.feed(source)
        self.close()
        if len(self.stack) != 1:
            raise ValueError(f"Unclosed <{self.stack[-1].tag}>")

    def handle_starttag(self, tag, attrs):
        node = Element(tag, dict(attrs), self.get_starttag_text(), self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(
            Element(tag, dict(attrs), self.get_starttag_text(), self.stack[-1]))

    def handle_endtag(self, tag):
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            raise ValueError(f"Unexpected closing tag </{tag}>")
        self.stack.pop().end = f"</{tag}>"

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")

    def handle_comment(self, data):
        self.handle_data(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.handle_data(f"<!{decl}>")


def ancestors(node):
    while node.parent:
        node = node.parent
        yield node


def normalize(source):
    root = Document(source).root
    nodes = list(root.walk())
    refs = {}
    for node in nodes:
        if node.has("footnote-ref") and node.attrs.get("id"):
            target = node.attrs.get("href", "").split("#")[-1]
            refs.setdefault(target, []).append(node)
    rank = {key: i for i, key in enumerate(refs)}
    notes = [n for n in nodes if n.tag == "div"
             and re.fullmatch(r"fn\d+", n.attrs.get("id", ""))
             and any(p.has("column-margin") for p in ancestors(n))]
    for note in notes:
        markers = refs.get(note.attrs["id"])
        if not markers:
            raise ValueError(f"No reference for {note.attrs['id']}")
        note.set("data-note-refs", " ".join(m.attrs["id"] for m in markers))
        closed = all(any(p.has("callout-collapse") and not p.has("show")
                         for p in ancestors(m)) for m in markers)
        if closed:
            note.set("hidden", None)
        if not any(n.has("footnote-back") for n in note.walk()):
            target = next((n for n in reversed(list(note.walk())) if n.tag == "p"), note)
            target.children.append(
                f' <a href="#{escape(markers[0].attrs["id"], quote=True)}" '
                'class="footnote-back" role="doc-backlink" '
                'aria-label="Back to reference">↩︎</a>')

    # Reorder only adjacent note-only containers, never across body content,
    # captions or asides. Also handle multiple notes within one container.
    note_set = set(notes)
    def note_container(node):
        return isinstance(node, Element) and node.has("column-margin") and all(
            c in note_set if isinstance(c, Element) else not c.strip()
            for c in node.children) and any(c in note_set for c in node.children
                                          if isinstance(c, Element))

    for parent in nodes:
        slots = []
        def flush():
            targets = []
            for i in slots:
                child = parent.children[i]
                if child in note_set:
                    targets.append((parent, i))
                else:
                    targets.extend((child, j) for j, n in enumerate(child.children)
                                   if isinstance(n, Element) and n in note_set)
            ordered = sorted((p.children[i] for p, i in targets),
                             key=lambda n: rank[n.attrs["id"]])
            for (p, i), node in zip(targets, ordered):
                p.children[i] = node
                node.parent = p
            slots.clear()
        for i, child in enumerate(parent.children):
            if isinstance(child, str) and not child.strip():
                continue
            if isinstance(child, Element) and (child in note_set or note_container(child)):
                slots.append(i)
            else:
                flush()
        flush()

    for solution in (n for n in nodes if n.has("solution") and n.has("callout")):
        header = next(n for n in solution.walk() if n.has("callout-header"))
        header.tag = "button"
        header.end = "</button>"
        header.set("type", "button")
        opened = header.attrs.get("aria-expanded") == "true"
        header.set("aria-label", "Hide solution" if opened else "Reveal solution")
        for child in header.walk():
            if child.tag == "div":
                child.tag = "span"
                child.end = "</span>"
                child.set("class", child.attrs.get("class", ""))
            if child.has("callout-title-container"):
                child.children = ["Hide" if opened else "Click to reveal"]
    return root.html()


def main():
    output = Path(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR") or
                  Path(__file__).resolve().parent / "_site")
    count = 0
    for path in sorted(output.rglob("*.html")):
        source = path.read_text(encoding="utf-8")
        if 'class="footnote-ref"' not in source and 'class="callout-header' not in source:
            continue
        try:
            result = normalize(source)
        except (ValueError, StopIteration) as exc:
            raise ValueError(f"{path}: unsupported Quarto markup: {exc}") from exc
        if result != source:
            path.write_text(result, encoding="utf-8")
            count += 1
    print(f"[notes] Normalized {count} page(s).")


if __name__ == "__main__":
    main()
