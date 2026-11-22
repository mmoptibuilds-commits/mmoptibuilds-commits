#!/usr/bin/env python3
"""Builds the profile header: my name, rolling through the languages I speak.

    pip install fonttools uharfbuzz
    python3 tools/gen-assets.py

Writes assets/header-light.svg and assets/header-dark.svg at the repo root.
Fonts are downloaded once from google/fonts into tools/.font-cache/ (ignored
by git). Each name is shaped here with HarfBuzz and stored as outlines, so
conjuncts and joins come out right on every viewer and no font is shipped.
Typefaces (all SIL Open Font License 1.1): Schibsted Grotesk, Noto Sans
Devanagari, Noto Nastaliq Urdu, Noto Sans Kannada and Noto Sans JP.
"""
import io
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CACHE = Path(__file__).resolve().parent / ".font-cache"
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/"

# (language, name, font path in google/fonts, axes, size px, tracking px)
NAMES = [
    ("English", "Mohammed Miran", "schibstedgrotesk/SchibstedGrotesk[wght].ttf", {"wght": 760}, 118, -4.8),
    ("Hindi", "मोहम्मद मीरान", "notosansdevanagari/NotoSansDevanagari[wdth,wght].ttf", {"wght": 700, "wdth": 100}, 104, 0),
    ("Japanese", "モハメド・ミラン", "notosansjp/NotoSansJP[wght].ttf", {"wght": 800}, 104, -2.0),
    ("Urdu", "محمد میران", "notonastaliqurdu/NotoNastaliqUrdu[wght].ttf", {"wght": 700}, 78, 0),
    ("Kannada", "ಮೊಹಮ್ಮದ್ ಮೀರಾನ್", "notosanskannada/NotoSansKannada[wdth,wght].ttf", {"wght": 700, "wdth": 100}, 94, 0),
    ("Japanese", "モハメド・ミラン", "notosansjp/NotoSansJP[wght].ttf", {"wght": 800}, 104, -2.0),
]

THEMES = {"light": "#1f2328", "dark": "#f0f6fc"}  # GitHub's own text colours

HOLD, MOVE = 2.2, 0.6  # seconds each name rests, seconds to roll to the next
BAND = 164             # height of the window the names roll through
BASELINE = 120         # shared baseline inside the band
GAP_BELOW = 26         # space between the header and the text under it


def load(path, axes):
    local = CACHE / path.replace("/", "__")
    if not local.exists():
        CACHE.mkdir(exist_ok=True)
        url = GF + path.replace("[", "%5B").replace("]", "%5D")
        urllib.request.urlretrieve(url, local)
    return instancer.instantiateVariableFont(TTFont(local), axes)


def to_bytes(font):
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def outline(font, text, size, track):
    """Shape text with HarfBuzz and return (svg path data, ink box)."""
    data = to_bytes(font)
    face = hb.Face(data)
    hbfont = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {})
    glyphs = TTFont(io.BytesIO(data)).getGlyphSet()
    order = TTFont(io.BytesIO(data)).getGlyphOrder()
    k = size / face.upem
    svgpen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    bounds = BoundsPen(glyphs)
    x = 0.0
    infos, positions = buf.glyph_infos, buf.glyph_positions
    for n, (info, pos) in enumerate(zip(infos, positions)):
        # font units, y up  ->  px, y down, baseline at 0
        m = (k, 0, 0, -k, (x + pos.x_offset) * k, -pos.y_offset * k)
        name = order[info.codepoint]
        glyphs[name].draw(TransformPen(svgpen, m))
        glyphs[name].draw(TransformPen(bounds, m))
        x += pos.x_advance + (track / k if n < len(infos) - 1 else 0)
    left, top, right, bottom = bounds.bounds  # px, y down
    return svgpen.getCommands(), left, right, -top, -bottom


def build():
    shaped = []
    for label, text, path, axes, size, track in NAMES:
        d, left, right, top, bottom = outline(load(path, axes), text, size, track)
        shaped.append(dict(label=label, text=text, d=d, left=left, right=right,
                           top=top, bottom=bottom))
    return shaped


def svg(shaped, color):
    pad = 6
    width = round(max(s["right"] - s["left"] for s in shaped) + 2 * pad)
    height = BAND + GAP_BELOW
    n = len(shaped)
    slot = HOLD + MOVE
    cycle = slot * n
    p = lambda sec: f"{sec / cycle * 100:.3f}%"
    # one keyframe for every name; delays put each one in its own slot
    keys = (
        f"@keyframes roll{{"
        f"0%{{transform:translateY(0);opacity:1;animation-timing-function:cubic-bezier(.6,0,.4,1)}}"
        f"{p(HOLD)}{{transform:translateY(0);opacity:1;animation-timing-function:cubic-bezier(.6,0,.4,1)}}"
        f"{p(slot)}{{transform:translateY(-{BAND}px);opacity:0}}"
        f"{p(slot + 0.001)}{{transform:translateY({BAND}px);opacity:0}}"
        f"{p(cycle - MOVE)}{{transform:translateY({BAND}px);opacity:0;animation-timing-function:cubic-bezier(.2,.7,.2,1)}}"
        f"100%{{transform:translateY(0);opacity:1}}}}"
    )
    rules, texts = [f"path{{fill:{color}}}"], []
    for i, s in enumerate(shaped):
        delay = i * slot - cycle if i else 0
        rules.append(
            f".n{i}{{animation:roll {cycle:.1f}s {delay:.1f}s infinite both;"
            + ("" if i == 0 else f"transform:translateY({BAND}px);opacity:0;") + "}"
        )
        # HarfBuzz lays out RTL runs in visual order too, so one rule
        # left-aligns every script.
        x = pad - s["left"]
        texts.append(f'<g class="n{i}"><path transform="translate({x:.1f} {BASELINE})" d="{s["d"]}"/></g>')
    still = "@media (prefers-reduced-motion: reduce){[class^=n]{animation:none}}"
    langs = ", ".join(s["label"] for s in shaped)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Mohammed Miran">
<title>Mohammed Miran</title>
<desc>My name in {escape(langs)}.</desc>
<defs><clipPath id="band"><rect width="{width}" height="{BAND}"/></clipPath></defs>
<style>
{keys}
{''.join(rules)}
{still}
</style>
<g clip-path="url(#band)">
{chr(10).join(texts)}
</g>
</svg>
"""


def main():
    shaped = build()
    for s in shaped:  # every name must sit inside the band, or it gets clipped
        assert BASELINE - s["top"] >= 2 and BASELINE - s["bottom"] <= BAND - 2, s["label"]
    for s in shaped:
        print(f"{s['label']:9} ink x {s['left']:7.1f}..{s['right']:7.1f}  y {s['bottom']:6.1f}..{s['top']:6.1f}")
    for mode, color in THEMES.items():
        ASSETS.mkdir(parents=True, exist_ok=True)
        out = ASSETS / f"header-{mode}.svg"
        out.write_text(svg(shaped, color))
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
