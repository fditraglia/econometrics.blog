"""Structural regressions: run with python3 -m unittest discover -s tests."""
from pathlib import Path
import runpy
import unittest

normalize = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                              "tools-normalize-notes.py"))["normalize"]
Document = normalize.__globals__["Document"]


def marker(number, suffix=""):
    return f'<a class="footnote-ref" id="fnref{number}{suffix}" href="#fn{number}">note</a>'


def note(number):
    return f'<div id="fn{number}"><p>Note {number}</p></div>'


def margin(content):
    return '<div class="column-margin column-container">' + content + '</div>'


def fold(content, number=1):
    return f'''<div class="callout solution">
<div class="callout-header collapsed" aria-expanded="false"
 data-bs-toggle="collapse" data-bs-target="#collapse{number}" aria-controls="collapse{number}">
<div class="callout-title-container">Solution</div></div>
<div class="callout-collapse collapse" id="collapse{number}">{content}</div></div>'''


class NormalizeTests(unittest.TestCase):
    def elements(self, source):
        return list(Document(normalize(source)).root.walk())

    def test_reversed_hoisted_notes_and_grouped_notes(self):
        source = fold(marker(1) + marker(2) + marker(3)) + margin(note(3)) + margin(note(2) + note(1))
        nodes = self.elements(source)
        notes = [n for n in nodes if "data-note-refs" in n.attrs]
        self.assertEqual([n.attrs["id"] for n in notes], ["fn1", "fn2", "fn3"])
        self.assertTrue(all("hidden" in n.attrs for n in notes))
        self.assertEqual(normalize(normalize(source)), normalize(source))

    def test_two_folds_and_unrelated_note_afterwards(self):
        source = (fold(marker(1)) + margin(note(1)) +
                  fold(marker(2), 2) + margin(note(2)) +
                  '<p>After both solutions.' + marker(3) + '</p>' + margin(note(3)))
        nodes = self.elements(source)
        notes = [n for n in nodes if "data-note-refs" in n.attrs]
        self.assertEqual(["hidden" in n.attrs for n in notes], [True, True, False])
        buttons = [n for n in nodes if n.tag == "button"]
        self.assertEqual(len(buttons), 2)
        self.assertTrue(all(n.attrs["type"] == "button" for n in buttons))
        self.assertTrue(all(not any(c.tag == "div" for c in n.walk()) for n in buttons))

    def test_interleaved_groups_are_sorted_across_containers(self):
        source = fold(marker(1) + marker(2) + marker(3)) + margin(note(3) + note(1)) + margin(note(2))
        notes = [n.attrs['id'] for n in self.elements(source) if 'data-note-refs' in n.attrs]
        self.assertEqual(notes, ['fn1', 'fn2', 'fn3'])

    def test_shared_note_with_visible_reference(self):
        source = marker(1) + fold(marker(1, '-1')) + margin(note(1))
        n = next(n for n in self.elements(source) if n.attrs.get("id") == "fn1")
        self.assertNotIn("hidden", n.attrs)
        self.assertEqual(n.attrs["data-note-refs"], "fnref1 fnref1-1")

    def test_do_not_move_notes_across_content(self):
        source = marker(1) + marker(2) + margin(note(2)) + '<p>Boundary</p>' + margin(note(1))
        result = normalize(source)
        self.assertLess(result.index('id="fn2"'), result.index('Boundary'))
        self.assertLess(result.index('Boundary'), result.index('id="fn1"'))

    def test_preserve_math_and_scripts(self):
        source = '<!DOCTYPE html><html><head><script>if (x < 2) { y = "&amp;"; }</script></head><body><p>\\(x &lt; y\\)</p></body></html>'
        self.assertEqual(normalize(source), source)


if __name__ == "__main__":
    unittest.main()
