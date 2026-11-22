#!/usr/bin/env python3
"""Generates every SVG used by the GitHub profile README (dark + light)."""
from pathlib import Path
from xml.sax.saxutils import escape as esc

OUT = Path(__file__).parent / "out" / "assets"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI Variable Display', 'Segoe UI', Inter, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', 'JetBrains Mono', 'Cascadia Code', Menlo, Consolas, 'DejaVu Sans Mono', monospace"
MONO_CW = 0.61  # monospace advance width per em (conservative)

THEMES = {
    "dark": dict(
        page="#0d1117", panel="#0f141b", card="#11171f", border="#232a33", grid="#1c232c",
        text="#e6edf3", muted="#9aa5b1", faint="#6b7581", sub="#8b96a3",
        accent="#f2a65a", accent2="#7ee0c3", blue="#82b8ff", grey="#9aa5b1",
        chip_bg="#161d26", chip_text="#c9d3dd", chip_border="#2a333e",
    ),
    "light": dict(
        page="#ffffff", panel="#fbfaf8", card="#fbfaf8", border="#e3ddd4", grid="#ece6dc",
        text="#1f2328", muted="#545e69", faint="#7a838d", sub="#5e6873",
        accent="#a8480f", accent2="#0b6b61", blue="#1f5fbf", grey="#5f6a75",
        chip_bg="#f3eee6", chip_text="#3a434c", chip_border="#e0d8cc",
    ),
}

REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def svg(w, h, body, title, style=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{esc(title)}" fill="none">\n<title>{esc(title)}</title>\n'
        f"<style>{style}{REDUCED}</style>\n{body}\n</svg>\n"
    )


def chip_w(label, size=11, pad=10):
    return round(len(label) * size * MONO_CW + pad * 2)


def chips(labels, x, y, t, size=11, h=22, gap=6, max_x=None):
    out, cx, cy = [], x, y
    for lab in labels:
        w = chip_w(lab, size)
        if max_x and cx + w > max_x:
            cx, cy = x, cy + h + gap
        out.append(
            f'<rect x="{cx}" y="{cy}" width="{w}" height="{h}" rx="{h/2}" fill="{t["chip_bg"]}" stroke="{t["chip_border"]}"/>'
            f'<text x="{cx + w/2}" y="{cy + h/2 + size*0.36:.1f}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="{size}" fill="{t["chip_text"]}">{esc(lab)}</text>'
        )
        cx += w + gap
    return "".join(out), cy + h


# ---------------------------------------------------------------- header
def header(t, mode):
    W, H = 1200, 340
    cx, cy = 980, 170
    rings = []
    for i, r in enumerate([40, 72, 104, 136, 168, 200]):
        op = 0.85 - i * 0.12
        dash = "" if i % 2 == 0 else ' stroke-dasharray="2 7"'
        rings.append(f'<circle r="{r}" stroke="{t["faint"]}" stroke-opacity="{op:.2f}"{dash}/>')
    style = (
        f".spin{{animation:spin 48s linear infinite}}.spin2{{animation:spin 30s linear infinite reverse}}"
        f"@keyframes spin{{to{{transform:rotate(360deg)}}}}"
        f".blink{{animation:blink 1.1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}"
        f".pulse{{animation:pulse 2.6s ease-in-out infinite}}@keyframes pulse{{50%{{opacity:.35}}}}"
        f".drift{{animation:drift 14s ease-in-out infinite alternate}}@keyframes drift{{to{{transform:translateX(-60px)}}}}"
    )
    body = f"""
<defs>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="{t['grid']}"/></pattern>
  <linearGradient id="fade" x1="0" x2="1"><stop offset="0.35" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>
  <mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
  <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{t['accent']}" stop-opacity="{0.22 if mode=='dark' else 0.14}"/><stop offset="1" stop-color="{t['accent']}" stop-opacity="0"/></radialGradient>
  <clipPath id="clip"><rect width="{W}" height="{H}" rx="20"/></clipPath>
</defs>
<g clip-path="url(#clip)">
  <rect width="{W}" height="{H}" fill="{t['panel']}"/>
  <rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#m)"/>
  <g class="drift"><circle cx="{cx}" cy="{cy}" r="260" fill="url(#glow)"/></g>
  <g transform="translate({cx} {cy})">
    {''.join(rings)}
    <g class="spin"><circle cx="104" cy="0" r="5" fill="{t['accent']}"/><circle cx="-168" cy="0" r="3.5" fill="{t['accent2']}"/></g>
    <g class="spin2"><circle cx="0" cy="-136" r="4" fill="{t['text']}" fill-opacity="0.8"/><circle cx="0" cy="72" r="3" fill="{t['accent']}" fill-opacity="0.7"/></g>
    <circle r="9" fill="{t['accent']}"/><circle r="18" stroke="{t['accent']}" stroke-opacity="0.45"/>
  </g>
</g>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="19.5" stroke="{t['border']}"/>
<circle class="pulse" cx="72" cy="78" r="5" fill="{t['accent2']}"/>
<text x="88" y="83" font-family="{MONO}" font-size="15" letter-spacing="0.5" fill="{t['muted']}">mmoptibuilds &#183; bengaluru, india</text>
<text x="64" y="172" font-family="{SANS}" font-size="70" font-weight="700" letter-spacing="-2" fill="{t['text']}">Mohammed Miran</text>
<text x="66" y="222" font-family="{SANS}" font-size="22" fill="{t['muted']}"><tspan fill="{t['accent']}" font-weight="600">AI-first builder.</tspan> Local-first apps, web products, infrastructure.</text>
<text x="66" y="280" font-family="{MONO}" font-size="14" fill="{t['sub']}">$ ship --verified --accessible --no-fake-claims<tspan class="blink" fill="{t['accent']}"> &#9608;</tspan></text>
"""
    return svg(W, H, body, "Mohammed Miran. AI-first builder in Bengaluru, India.", style)


# ---------------------------------------------------------------- cards
STATUS_COLOR = {"shipped": "accent2", "live": "blue", "paused": "grey"}

CARDS = [
    dict(slug="notes", title="Notes", sub="Flutter · Android + Linux", status=("v1.1.0 · shipped", "shipped"),
         body=["Offline-first notes in an encrypted local database.",
               "Pair devices by QR and sync peer-to-peer over LAN,",
               "no account, no relay. Ed25519-signed releases."],
         chips=["Flutter", "Dart", "SQLite", "LAN sync", "Ed25519"]),
    dict(slug="markdown-reader", title="Markdown Reader", sub="Browser extension · MV3", status=("v1.0.0 · shipped", "shipped"),
         body=["Local-first Markdown reader for Chrome, Edge,",
               "Vivaldi and Firefox. KaTeX, Mermaid, Graphviz,",
               "folder workspaces. No backend, no telemetry."],
         chips=["WXT", "React", "TypeScript", "Playwright", "axe"]),
    dict(slug="coldharbour", title="Coldharbour", sub="Full-stack demo product", status=("live demo", "live"),
         body=["Evidence-first cold-chain monitoring for clinical",
               "shipments. Telemetry exploration, motion design,",
               "accessibility and SEO. Fictional data, real build."],
         chips=["Next.js", "PostgreSQL", "Drizzle", "GSAP"]),
    dict(slug="mmoptibuilds", title="mmoptibuilds", sub="Business platform · Systems + Studio", status=("deployed", "live"),
         body=["One platform, two divisions with their own design",
               "systems. Owner console, enquiry storage, SEO and",
               "a nine-gate verification pipeline."],
         chips=["Next.js", "TypeScript", "Vercel", "Playwright"]),
    dict(slug="upload-portal", title="Client Upload Portal", sub="upload.mmoptibuilds.com", status=("shipped", "shipped"),
         body=["Protected client-to-admin file delivery with",
               "authenticated user and admin flows, a resumable",
               "upload architecture and upload history."],
         chips=["Next.js", "TypeScript", "Auth", "Drive"]),
    dict(slug="hearth-os", title="Hearth OS", sub="Installable browser desktop", status=("paused", "paused"),
         body=["Local-first personal desktop in the browser:",
               "floating windows, widgets, iOS-style mobile sheets,",
               "Dexie persistence and offline PWA support."],
         chips=["React", "Vite", "Dexie", "Workbox", "Vitest"]),
]


def card(c, t):
    W, H = 480, 212
    label, kind = c["status"]
    col = t[STATUS_COLOR[kind]]
    pw = chip_w(label.upper(), 10, 12) + 14
    chip_svg, _ = chips(c["chips"], 24, H - 44, t, max_x=W - 56)
    lines = "".join(
        f'<text x="24" y="{104 + i*21}" font-family="{SANS}" font-size="14.5" fill="{t["muted"]}">{esc(l)}</text>'
        for i, l in enumerate(c["body"])
    )
    body = f"""
<defs><linearGradient id="top{t['_m']}" x1="0" x2="1"><stop offset="0" stop-color="{col}"/><stop offset="0.6" stop-color="{col}" stop-opacity="0"/></linearGradient>
<clipPath id="c{t['_m']}"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>
<g clip-path="url(#c{t['_m']})"><rect width="{W}" height="{H}" fill="{t['card']}"/><rect width="{W}" height="2" fill="url(#top{t['_m']})"/></g>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="13.5" stroke="{t['border']}"/>
<text x="24" y="46" font-family="{SANS}" font-size="23" font-weight="700" letter-spacing="-0.4" fill="{t['text']}">{esc(c['title'])}</text>
<text x="24" y="69" font-family="{MONO}" font-size="12" fill="{t['sub']}">{esc(c['sub'])}</text>
<rect x="{W-24-pw}" y="25" width="{pw}" height="24" rx="12" fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-opacity="0.45"/>
<circle cx="{W-24-pw+13}" cy="37" r="3.5" fill="{col}"/>
<text x="{W-24-pw+22}" y="40.6" font-family="{MONO}" font-size="10" font-weight="600" letter-spacing="0.6" fill="{col}">{esc(label.upper())}</text>
{lines}
{chip_svg}
<path d="M{W-38} {H-22} L{W-26} {H-34} M{W-35} {H-34} H{W-26} V{H-25}" stroke="{t['faint']}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
"""
    alt = f"{c['title']}: {' '.join(c['body'])} Status: {label}."
    return svg(W, H, body, alt)


# ---------------------------------------------------------------- stack
STACK = [
    ("PRODUCT & WEB", ["Next.js", "React", "TypeScript", "Tailwind", "Flutter", "Dart", "PostgreSQL", "Drizzle", "Supabase", "Dexie", "PWA", "WXT"]),
    ("QUALITY", ["Playwright", "Vitest", "axe", "responsive QA", "perf budgets", "Vercel", "Cloudflare"]),
    ("INFRA", ["Linux", "Docker", "Portainer", "SSH", "DNS", "Cloudflare Tunnel", "Tailscale", "self-hosting"]),
    ("AI WORKFLOW", ["Claude Code", "Codex", "Gemini", "OpenCode", "MCP", "Ollama", "multi-model review"]),
]


def stack(t):
    W = 980
    y, rows = 32, []
    for label, items in STACK:
        rows.append(f'<text x="32" y="{y+15}" font-family="{MONO}" font-size="11.5" font-weight="600" letter-spacing="1.2" fill="{t["accent"]}">{esc(label)}</text>')
        s, bottom = chips(items, 200, y, t, size=12, h=24, gap=8, max_x=W - 32)
        rows.append(s)
        y = bottom + 20
    H = y + 8
    body = (f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="{t["card"]}" stroke="{t["border"]}"/>' + "".join(rows))
    alt = "Tech stack. " + " ".join(f"{l.title()}: {', '.join(i)}." for l, i in STACK)
    return svg(W, H, body, alt)


# ---------------------------------------------------------------- socials
def icon(kind, t, x, y):
    s = t["text"]
    if kind == "web":
        return (f'<g transform="translate({x} {y})" stroke="{s}" stroke-width="1.5"><circle cx="8" cy="8" r="7"/>'
                f'<ellipse cx="8" cy="8" rx="3" ry="7"/><path d="M1 8h14"/></g>')
    if kind == "x":
        return (f'<g transform="translate({x} {y}) scale(0.667)"><path fill="{s}" d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/></g>')
    if kind == "ig":
        return (f'<g transform="translate({x} {y})" stroke="{s}" stroke-width="1.5"><rect x="1" y="1" width="14" height="14" rx="4"/>'
                f'<circle cx="8" cy="8" r="3.2"/><circle cx="12" cy="4" r="0.6" fill="{s}"/></g>')
    if kind == "threads":
        return (f'<text x="{x+8}" y="{y+13}" text-anchor="middle" font-family="{SANS}" font-size="17" font-weight="600" fill="{s}">@</text>')
    if kind == "mail":
        return (f'<g transform="translate({x} {y})" stroke="{s}" stroke-width="1.5" stroke-linejoin="round"><rect x="1" y="3" width="14" height="10" rx="2"/>'
                f'<path d="M1.5 4l6.5 5 6.5-5"/></g>')


SOCIALS = [("web", "mmoptibuilds.com"), ("x", "X"), ("ig", "Instagram"), ("threads", "Threads"), ("mail", "Email")]


def social(kind, label, t):
    tw = round(len(label) * 13 * 0.6)
    W, H = 18 + 16 + 10 + tw + 18, 40
    body = (f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="20" fill="{t["card"]}" stroke="{t["border"]}"/>'
            + icon(kind, t, 18, 12)
            + f'<text x="44" y="24.5" font-family="{SANS}" font-size="13" font-weight="500" fill="{t["text"]}">{esc(label)}</text>')
    return svg(W, H, body, label)


ADAPT = ".d{display:none}@media (prefers-color-scheme: dark){.l{display:none}.d{display:inline}}"


def adaptive(fn, *args):
    """One SVG holding both themes; the viewer's color scheme picks one."""
    import re
    parts = {}
    for mode in ("light", "dark"):
        t = dict(THEMES[mode], _m=mode[0])
        parts[mode] = fn(*args, t)
    head = re.match(r"(<svg[^>]*>\n<title>.*?</title>\n)<style>(.*?)</style>\n", parts["light"], re.S)
    inner = {m: re.sub(r"^<svg[^>]*>\n<title>.*?</title>\n<style>.*?</style>\n|\n</svg>\n$", "", p, flags=re.S) for m, p in parts.items()}
    return (head.group(1) + f"<style>{head.group(2)}{ADAPT}</style>\n"
            + f'<g class="l">{inner["light"]}</g>\n<g class="d">{inner["dark"]}</g>\n</svg>\n')


def main():
    import shutil
    shutil.rmtree(OUT, ignore_errors=True)
    (OUT / "cards").mkdir(parents=True)
    (OUT / "socials").mkdir(parents=True)
    for c in CARDS:
        (OUT / "cards" / f"{c['slug']}.svg").write_text(adaptive(card, c))
    for kind, label in SOCIALS:
        (OUT / "socials" / f"{kind}.svg").write_text(adaptive(social, kind, label))
    for mode, t in THEMES.items():
        (OUT / f"header-{mode}.svg").write_text(header(t, mode))
        (OUT / f"stack-{mode}.svg").write_text(stack(t))


if __name__ == "__main__":
    main()
