# /// script
# dependencies = ["fonttools", "brotli"]
# ///
"""Build the subset woff2 files embedded into figure SVGs.

Re-run this only if the glyph coverage below proves insufficient. Output goes to
fonts/subset/ and is committed; the render does not depend on Python.
"""
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
import io
import pathlib

FONTS = pathlib.Path("fonts")
OUT = FONTS / "subset"
OUT.mkdir(exist_ok=True)

# Axis labels, legends, titles and plotmath output. Deliberately generous: the
# cost of an unused glyph is bytes, the cost of a missing one is tofu.
CHARS = (
    " !\"#$%&'()*+,-./0123456789:;<=>?@[\\]^_`{|}~"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "−×·√∑∏∫∞≤≥≠≈±∓∝∂∇⊥∥"
    # full basic Greek: plotmath emits these as Unicode, and R labels them with
    # font-family "Symbol", which the fig.process hook redirects to the serif.
    "αβγδεζηθικλμνξοπρςστυφχψω"
    "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    "ϑϕϖϒϱς"
    "̄̂̃̇′″←→↔⇒"
    "‘’“”–—…"
)

# Both faces ship as variable fonts. Carrying their weight and optical-size
# axes into every figure costs ~6x the bytes for axes no figure varies, so pin
# a single regular instance first. Figures use no italic and no bold except the
# DAG node labels, whose synthetic bold is acceptable at that size.
INSTANCE = {"wght": 400, "opsz": 11}

for src, label in [("jetbrains-mono-latin-normal.woff2", "mono"),
                   ("source-serif-4-latin-normal.woff2", "serif")]:
    dst = OUT / f"{label}.woff2"
    font = TTFont(FONTS / src)
    axes = {a.axisTag for a in font["fvar"].axes} if "fvar" in font else set()
    pin = {k: v for k, v in INSTANCE.items() if k in axes}

    if pin:
        static = instancer.instantiateVariableFont(TTFont(FONTS / src), pin)
        buf = io.BytesIO()
        static.save(buf)
        buf.seek(0)
        tmp = OUT / f".{label}-instance.ttf"
        tmp.write_bytes(buf.read())
        source = tmp
    else:
        source, tmp = FONTS / src, None

    subset.main([
        str(source), f"--text={CHARS}", "--flavor=woff2",
        f"--output-file={dst}", "--layout-features=*", "--no-hinting",
    ])
    if tmp:
        tmp.unlink()
    print(f"{label:6s} {(FONTS/src).stat().st_size/1024:6.1f} KB "
          f"-> {dst.stat().st_size/1024:5.1f} KB  (pinned {pin or 'n/a'})")
