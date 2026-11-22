#!/usr/bin/env python3
"""Builds the profile images: the animated header, one row per project, the
tool strip and the contact panel.

    pip install fonttools uharfbuzz
    python3 tools/gen-assets.py

Writes assets/<name>.<hash>.svg and points README.md at the new files, so GitHub's
image cache never serves a stale copy. Fonts are downloaded once from google/fonts
into tools/.font-cache/ (ignored by git). Every string is shaped here with
HarfBuzz and stored as outlines, so no font is shipped and every viewer draws the
same shapes. Typefaces (all SIL Open Font License 1.1): Schibsted Grotesk, Noto
Sans Devanagari, Noto Nastaliq Urdu, Noto Sans Kannada and Noto Sans JP.
"""
import hashlib
import io
import re
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


_FONTS = {}


def load(path, axes):
    key = (path, tuple(sorted(axes.items())))
    if key not in _FONTS:
        _FONTS[key] = _load(path, axes)
    return _FONTS[key]


def _load(path, axes):
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


# ---------------------------------------------------------------- shared bits
LATIN = "schibstedgrotesk/SchibstedGrotesk[wght].ttf"
YIN = "M0,-100A100,100 0 0 1 0,100A50,50 0 0 1 0,0A50,50 0 0 0 0,-100Z"
_cap = {}


def latin(text, size, wght, track=0.0):
    return outline(load(LATIN, {"wght": wght}), text, size, track)


def cap_height(size, wght):
    """Height of a capital letter, so every row shares one baseline."""
    key = (size, wght)
    if key not in _cap:
        _cap[key] = latin("H", size, wght)[3]
    return _cap[key]


def yinyang(cx, cy, r, ink, bone, rot=0.0, ring=True):
    return (
        f'<g transform="translate({cx} {cy}) rotate({rot}) scale({r / 100:.4f})">'
        f'<circle r="100" fill="{bone}"/><path d="{YIN}" fill="{ink}"/>'
        f'<circle cy="-50" r="14" fill="{ink}"/><circle cy="50" r="14" fill="{bone}"/>'
        + (f'<circle r="100" fill="none" stroke="{ink}" stroke-width="1.6"/>' if ring else "")
        + "</g>"
    )


def wrap(title, desc, w, h, defs, body, style=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n<desc>{escape(desc)}</desc>\n"
        f"<defs>{defs}</defs>\n" + (f"<style>{style}</style>\n" if style else "") + body + "\n</svg>\n"
    )


# ---------------------------------------------------------------- project rows
ROW_W, ROW_H, PILL_H = 800, 108, 54
ROWS = [  # file, name, status, version, dimmed
    ("row-notes", "Notes", "Released", "v1.1.0", False),
    ("row-markdown-reader", "Markdown Reader", "Finished", "v1.0.0", False),
    ("row-coldharbour", "Coldharbour", "Demo", "", False),
    ("row-mmoptibuilds-com", "mmoptibuilds.com", "Live", "", False),
    ("row-upload-portal", "Client Upload Portal", "Finished", "", False),
    ("row-hearth-os", "Hearth OS", "Paused", "", True),
]


def row(name, status, version, dim):
    base = ROW_H / 2 + cap_height(52, 720) / 2
    d, left, right, _, _ = latin(name, 52, 720, -1.4)
    fade = ' fill-opacity=".42"' if dim else ""
    parts = [
        f'<rect width="{ROW_W}" height="{ROW_H}" rx="24" fill="{BONE}"/>',
        f'<path transform="translate({36 - left:.1f} {base:.1f})" d="{d}" fill="{INK}"{fade}/>',
    ]
    sd, sl, sr, _, _ = latin(status, 28, 640)
    pw = (sr - sl) + 48
    px = ROW_W - 36 - pw
    py = (ROW_H - PILL_H) / 2
    sbase = ROW_H / 2 + cap_height(28, 640) / 2
    if dim:
        parts.append(f'<rect x="{px:.1f}" y="{py}" width="{pw:.1f}" height="{PILL_H}" rx="{PILL_H / 2}" '
                     f'fill="none" stroke="{INK}" stroke-opacity=".5" stroke-width="2.5"/>')
        parts.append(f'<path transform="translate({px + 24 - sl:.1f} {sbase:.1f})" d="{sd}" fill="{INK}" fill-opacity=".6"/>')
    else:
        parts.append(f'<rect x="{px:.1f}" y="{py}" width="{pw:.1f}" height="{PILL_H}" rx="{PILL_H / 2}" fill="{INK}"/>')
        parts.append(f'<path transform="translate({px + 24 - sl:.1f} {sbase:.1f})" d="{sd}" fill="{BONE}"/>')
    if version:
        vd, vl, vr, _, _ = latin(version, 28, 520)
        parts.append(f'<path transform="translate({px - 22 - vr:.1f} {sbase:.1f})" d="{vd}" fill="{INK}" fill-opacity=".62"/>')
    label = f"{name}, {status.lower()}" + (f", {version}" if version else "")
    return wrap(label, f"Project: {label}.", ROW_W, ROW_H, "", "\n".join(parts))


# ---------------------------------------------------------------- tool strip
TOOLS = ["Next.js", "React", "TypeScript", "Tailwind CSS", "Vite", "Flutter", "Dart", "WXT",
         "PostgreSQL", "Drizzle", "Supabase", "SQLite", "Dexie", "Playwright", "Vitest", "axe",
         "Vercel", "Cloudflare", "Docker", "Tailscale", "Claude Code", "Codex", "Gemini",
         "OpenCode", "Ollama", "MCP"]
STRIP_W, STRIP_H, STRIP_GAP, STRIP_SPEED, STRIP_PAD = 800, 128, 46, 42, 120   # px, px, px between items, px per second


def tools_strip():
    size, wght = 40, 620
    base = STRIP_H / 2 + cap_height(size, wght) / 2
    x, items = 0.0, []
    for t in TOOLS:
        d, l, r, _, _ = latin(t, size, wght, -0.6)
        items.append(f'<path transform="translate({x - l:.1f} {base:.1f})" d="{d}" fill="{BONE}"/>')
        x += (r - l) + STRIP_GAP
        items.append(yinyang(f"{x - STRIP_GAP / 2:.1f}", STRIP_H / 2, 10, INK, BONE, 0, ring=False)
                     .replace("</g>", f'<circle r="100" fill="none" stroke="{BONE}" stroke-width="8"/></g>'))
    total = x
    dur = total / STRIP_SPEED
    style = (f"@keyframes run{{to{{transform:translateX(-{total:.1f}px)}}}}"
             f".m{{animation:run {dur:.1f}s linear infinite}}"
             "@media (prefers-reduced-motion: reduce){.m{animation:none}}")
    defs = (f'<g id="s">{"".join(items)}</g>'
            f'<clipPath id="p"><rect width="{STRIP_W}" height="{STRIP_H}" rx="24"/></clipPath>'
            f'<linearGradient id="l"><stop offset="0" stop-color="{INK}"/><stop offset="1" stop-color="{INK}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="r"><stop offset="0" stop-color="{INK}" stop-opacity="0"/><stop offset="1" stop-color="{INK}"/></linearGradient>')
    body = (f'<g clip-path="url(#p)"><rect width="{STRIP_W}" height="{STRIP_H}" fill="{INK}"/>'
            f'<g class="m"><use xlink:href="#s" x="{STRIP_PAD}"/><use xlink:href="#s" x="{total + STRIP_PAD:.1f}"/><use xlink:href="#s" x="{2 * total + STRIP_PAD:.1f}"/></g>'
            f'<rect width="110" height="{STRIP_H}" fill="url(#l)"/><rect x="{STRIP_W - 110}" width="110" height="{STRIP_H}" fill="url(#r)"/></g>')
    return wrap("Tools I use", "A slow strip of tool names: " + ", ".join(TOOLS) + ".", STRIP_W, STRIP_H, defs, body, style)


# ---------------------------------------------------------------- contact panel
CON_W, CON_H = 800, 250


def contact():
    d1, l1, _, _, _ = latin("Need a website or hardware for a small business?", 29, 520)
    d2, l2, _, _, _ = latin("hello@mmoptibuilds.com", 58, 740, -1.6)
    defs = f'<clipPath id="p"><rect width="{CON_W}" height="{CON_H}" rx="26"/></clipPath>'
    body = (f'<g clip-path="url(#p)"><rect width="{CON_W}" height="{CON_H}" fill="{BONE}"/>'
            + yinyang(700, 150, 205, INK, BONE, -28, ring=False)
            + f'<g style="mix-blend-mode:difference">'
              f'<path transform="translate({40 - l1:.1f} 96)" d="{d1}" fill="{TEXT}"/>'
              f'<path transform="translate({40 - l2:.1f} 170)" d="{d2}" fill="{TEXT}"/></g></g>')
    return wrap("Email hello@mmoptibuilds.com",
                "Need a website or hardware for a small business? hello@mmoptibuilds.com", CON_W, CON_H, defs, body)


# ---------------------------------------------------------------- output
def emit(name, text, readme):
    """Write assets/<name>.<hash>.svg, drop older copies, repoint README."""
    digest = hashlib.sha256(text.encode()).hexdigest()[:8]
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / f"{name}.{digest}.svg"
    out.write_text(text)
    for old in ASSETS.glob(f"{name}.*.svg"):
        if old != out:
            old.unlink()
    readme = re.sub(rf"assets/{re.escape(name)}\.[0-9a-f]{{8}}\.svg", f"assets/{out.name}", readme)
    print(f"{out.name:34} {out.stat().st_size / 1024:5.1f} KB")
    return readme


def main():
    shaped = build()
    for s in shaped:
        width = s["right"] - s["left"]
        s["scale"] = TARGET[s["label"]] / width
        h = (s["top"] - s["bottom"]) * s["scale"]
        assert h <= BAND - 20, f"{s['label']} is {h:.0f}px tall, band is {BAND}"
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    readme = emit("header", svg(shaped), readme)
    for name, label, status, version, dim in ROWS:
        readme = emit(name, row(label, status, version, dim), readme)
    readme = emit("tools", tools_strip(), readme)
    readme = emit("contact", contact(), readme)
    readme_path.write_text(readme)
    for stale in ASSETS.glob("*.svg"):
        if not re.search(r"\.[0-9a-f]{8}\.svg$", stale.name):
            stale.unlink()


if __name__ == "__main__":
    main()
