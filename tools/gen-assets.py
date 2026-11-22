#!/usr/bin/env python3
"""Builds the profile header: a yin-yang circle with my name turning through
the languages I speak, one line, inverting where it crosses the dark half.

    pip install fonttools uharfbuzz
    python3 tools/gen-assets.py

Writes assets/header.svg at the repo root. Fonts are downloaded once from
google/fonts into tools/.font-cache/ (ignored by git). Each name is shaped
here with HarfBuzz and stored as outlines, so conjuncts and joins come out
right on every viewer and no font is shipped. Typefaces (all SIL Open Font
License 1.1): Schibsted Grotesk, Noto Sans Devanagari, Noto Nastaliq Urdu,
Noto Sans Kannada and Noto Sans JP.
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

# canvas and scene
W, H = 1000, 380
CX, CY, R = 805, 190, 300          # circle centre and radius, bleeds off the panel
PAD = 56                           # left margin of the name
BAND = 250                         # window the names roll through
TARGET = {"English": 880, "Hindi": 620, "Japanese": 760, "Urdu": 430, "Kannada": 800}  # ink width px
BONE, INK = "#ebe8df", "#15171c"
# Colour of the text before blending. difference(text, bone) = ink on the light
# panel, and difference(text, ink) = a light tone over the dark half.
TEXT = "#d6d4cf"

HOLD, MOVE = 2.2, 0.6  # seconds each name rests, seconds to roll to the next
INTRO, DRIFT = 3.4, 120  # seconds for the opening spin, for one slow turn after it


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


def svg(shaped):
    n = len(shaped)
    slot = HOLD + MOVE
    cycle = slot * n
    p = lambda sec: f"{sec / cycle * 100:.3f}%"
    keys = (
        f"@keyframes roll{{"
        f"0%{{transform:translateY(0);opacity:1;animation-timing-function:cubic-bezier(.6,0,.4,1)}}"
        f"{p(HOLD)}{{transform:translateY(0);opacity:1;animation-timing-function:cubic-bezier(.6,0,.4,1)}}"
        f"{p(slot)}{{transform:translateY(-{BAND}px);opacity:0}}"
        f"{p(slot + 0.001)}{{transform:translateY({BAND}px);opacity:0}}"
        f"{p(cycle - MOVE)}{{transform:translateY({BAND}px);opacity:0;animation-timing-function:cubic-bezier(.2,.7,.2,1)}}"
        f"100%{{transform:translateY(0);opacity:1}}}}"
        f"@keyframes intro{{from{{transform:rotate(-540deg)}}to{{transform:rotate(0)}}}}"
        f"@keyframes drift{{to{{transform:rotate(360deg)}}}}"
    )
    rules = [
        f"path.t{{fill:{TEXT}}}",
        f".c{{transform-origin:{CX}px {CY}px}}",
        f".i{{animation:intro {INTRO}s cubic-bezier(.2,.7,.1,1) both}}",
        f".d{{animation:drift {DRIFT}s linear infinite}}",
    ]
    texts = []
    for i, s in enumerate(shaped):
        delay = i * slot - cycle if i else 0
        rules.append(
            f".n{i}{{animation:roll {cycle:.1f}s {delay:.1f}s infinite both;"
            + ("" if i == 0 else f"transform:translateY({BAND}px);opacity:0;") + "}"
        )
        k = s["scale"]
        x = PAD - s["left"] * k
        y = CY + (s["top"] + s["bottom"]) / 2 * k   # centre the ink on the circle's centre line
        texts.append(
            f'<g class="n{i}"><path class="t" transform="translate({x:.1f} {y:.1f}) scale({k:.4f})" d="{s["d"]}"/></g>'
        )
    still = "@media (prefers-reduced-motion: reduce){.i,.d,[class^=n]{animation:none}}"
    langs = ", ".join(dict.fromkeys(s["label"] for s in shaped))
    top = CY - BAND // 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Mohammed Miran">
<title>Mohammed Miran</title>
<desc>My name in {escape(langs)}, over a yin-yang circle that turns slowly.</desc>
<defs>
<clipPath id="panel"><rect width="{W}" height="{H}" rx="26"/></clipPath>
<clipPath id="band"><rect y="{top}" width="{W}" height="{BAND}"/></clipPath>
</defs>
<style>
{keys}
{''.join(rules)}
{still}
</style>
<g clip-path="url(#panel)">
<rect width="{W}" height="{H}" fill="{BONE}"/>
<g class="c i"><g class="c d"><g transform="translate({CX} {CY}) scale({R / 100})">
<circle r="100" fill="{BONE}"/>
<path d="M0,-100A100,100 0 0 1 0,100A50,50 0 0 1 0,0A50,50 0 0 0 0,-100Z" fill="{INK}"/>
<circle cy="-50" r="14" fill="{INK}"/><circle cy="50" r="14" fill="{BONE}"/>
<circle r="100" fill="none" stroke="{INK}" stroke-width="1.6"/>
</g></g></g>
<g style="mix-blend-mode:difference"><g clip-path="url(#band)">
{chr(10).join(texts)}
</g></g>
</g>
</svg>
"""


def main():
    shaped = build()
    for s in shaped:
        width = s["right"] - s["left"]
        s["scale"] = TARGET[s["label"]] / width
        h = (s["top"] - s["bottom"]) * s["scale"]
        assert h <= BAND - 20, f"{s['label']} is {h:.0f}px tall, band is {BAND}"
        print(f"{s['label']:9} scale {s['scale']:.2f}  ink {width * s['scale']:5.0f} x {h:4.0f}px")
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / "header.svg"
    out.write_text(svg(shaped))
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
