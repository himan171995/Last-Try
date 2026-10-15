"""Generate index.html (16:9, 60 s) for the piles Q&A edit from build/edit.json.

Run: python3 build/edl.py && python3 -I build/aroll.py source.mp4 && python3 build/compose.py

Layout: the doctor's footage plays in a framed panel on the right (near-native resolution of the
vertical source); the left column carries the chapter tag, explanatory graphics and captions.
Full-screen scenes (title cover, shloka, anatomy, dairy, rice, kapha, sweets, end screen) cut in
over the panel. Every graphic is anchored to a spoken word via at(). SFX cues go to build/sfx.json.
"""

import html
import json
import math
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EDIT = json.load(open(os.path.join(HERE, "edit.json")))
WORDS = EDIT["words"]
SECTIONS = {s["name"]: s for s in EDIT["sections"]}
SPEECH_END = EDIT["speech_duration"]
TOTAL = 60.0
W, H = 1920, 1080
rnd = random.Random(42)


def norm(w):
    return re.sub(r"[^a-z0-9\-]", "", w.lower())


def at(word, after=0.0):
    for w in WORDS:
        if norm(w["text"]) == word and w["start"] >= after - 1e-6:
            return round(w["start"], 3)
    raise KeyError(f"{word} after {after}")


def end_of(word, after=0.0):
    for w in WORDS:
        if norm(w["text"]) == word and w["start"] >= after - 1e-6:
            return round(w["end"], 3)
    raise KeyError(word)


def sec(name):
    return SECTIONS[name]["start"]


def sec_end(name):
    return SECTIONS[name]["end"]


def esc(s):
    return html.escape(s, quote=True)


def f(x):
    return f"{x:.3f}"


JS, SFX, BODY, FULL = [], [], [], []
_SEEN = set()


def tw(line):
    m = re.match(r'tl\.fromTo\("([^"]+)", (\{.*?\}), \{', line)
    if m:
        sel = m.group(1)
        if sel in _SEEN:
            line = line.replace(m.group(0), f'tl.fromTo("{sel}", {m.group(2)}, {{immediateRender:false, ', 1)
        _SEEN.add(sel)
    elif line.startswith("tl.to(") or line.startswith("tl.set("):
        _SEEN.add(re.match(r'tl\.\w+\("([^"]+)"', line).group(1))
    JS.append(line)


def sfx(name, t, vol=0.5):
    SFX.append({"file": f"assets/sfx/{name}.mp3", "start": round(max(0.0, t), 3), "volume": vol})


def clip(ident, start, end, inner, cls="", z=10, track=1):
    BODY.append(f'<div id="{ident}" class="clip {cls}" data-start="{f(start)}" data-duration="{f(end - start)}" '
                f'data-track-index="{track}" style="z-index:{z}">{inner}</div>')


def full(ident, start, end, inner, z=30, track=3):
    FULL.append((start, end))
    clip(ident, start, end, inner, "fullscene", z, track)


def icon(name, size, ident=None, cls=""):
    i = f' id="{ident}"' if ident else ""
    return f'<img{i} class="ico {cls}" src="assets/icons/{name}.webp" alt="" style="width:{size}px;height:{size}px" />'


def pop_in(sel, t, dur=0.45, scale=0.6, y=0):
    tw(f'tl.fromTo("{sel}", {{opacity:0, scale:{scale}, y:{y}}}, {{opacity:1, scale:1, y:0, duration:{dur}, ease:"back.out(2.2)"}}, {f(t)});')


def rise_in(sel, t, dur=0.5, y=40, stagger=0):
    st = f", stagger:{stagger}" if stagger else ""
    tw(f'tl.fromTo("{sel}", {{opacity:0, y:{y}}}, {{opacity:1, y:0, duration:{dur}, ease:"power3.out"{st}}}, {f(t)});')


def slide_in(sel, t, dur=0.5, x=-60):
    tw(f'tl.fromTo("{sel}", {{opacity:0, x:{x}}}, {{opacity:1, x:0, duration:{dur}, ease:"power3.out"}}, {f(t)});')


def fade_out(sel, t, dur=0.3, y=-20):
    tw(f'tl.to("{sel}", {{opacity:0, y:{y}, duration:{dur}, ease:"power2.in"}}, {f(t)});')


def iris_in(sel, t, dur=0.55, cx="50%", cy="45%"):
    tw(f'tl.fromTo("{sel}", {{clipPath:"circle(0% at {cx} {cy})"}}, {{clipPath:"circle(130% at {cx} {cy})", duration:{dur}, ease:"power3.inOut"}}, {f(t)});')


def wipe_in(sel, t, dur=0.5):
    tw(f'tl.fromTo("{sel}", {{clipPath:"inset(0% 100% 0% 0%)"}}, {{clipPath:"inset(0% 0% 0% 0%)", duration:{dur}, ease:"power3.inOut"}}, {f(t)});')


def wipe_out(sel, t, dur=0.4):
    tw(f'tl.fromTo("{sel}", {{clipPath:"inset(0% 0% 0% 0%)"}}, {{clipPath:"inset(0% 0% 0% 100%)", duration:{dur}, ease:"power3.in"}}, {f(t)});')


def leak(t, strength=0.7):
    tw(f'tl.fromTo("#leak", {{opacity:0, xPercent:-12}}, {{opacity:{strength}, xPercent:0, duration:0.16, ease:"power1.out"}}, {f(t - 0.12)});')
    tw(f'tl.to("#leak", {{opacity:0, xPercent:10, duration:0.45, ease:"power1.in"}}, {f(t + 0.05)});')


def side(ident, start, end, inner, z=12):
    """Left-column card; fades in/out by itself."""
    clip(ident, start, end, f'<div id="{ident}-in" class="side-card">{inner}</div>', "side", z, 2)
    rise_in(f"#{ident}-in", start, 0.5, 40)
    fade_out(f"#{ident}-in", end - 0.3, 0.28, -30)


def sanskrit(deva, roman):
    return f'<div class="skt"><div class="skt-deva">{deva}</div><div class="skt-rom">{esc(roman)}</div></div>'


# ------------------------------------------------------------------ anatomy kit
def hexagon(cx, cy, r):
    return " ".join(f"{cx + r * math.cos(math.radians(60 * k + 30)):.1f},{cy + r * math.sin(math.radians(60 * k + 30)):.1f}" for k in range(6))


def vessel(prefix, t0, t1, n_cells=20, n_hex=22, hex_from=0.0, hex_to=0.85, width=1920, height=260):
    dur = t1 - t0
    hgt = height
    parts = [
        f'<svg class="vessel" viewBox="0 0 {width} {hgt}" width="{width}" height="{hgt}">', "<defs>",
        f'<linearGradient id="{prefix}-vg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5b0d1c"/><stop offset="0.18" stop-color="#9e1f33"/>'
        '<stop offset="0.5" stop-color="#c0303f"/><stop offset="0.82" stop-color="#9e1f33"/><stop offset="1" stop-color="#4a0a17"/></linearGradient>',
        f'<radialGradient id="{prefix}-rbc" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#a51d2d"/><stop offset="0.45" stop-color="#d23c4a"/>'
        '<stop offset="0.8" stop-color="#ef5d63"/><stop offset="1" stop-color="#b52436"/></radialGradient>',
        f'<clipPath id="{prefix}-clip"><rect x="-300" y="14" width="{width + 600}" height="{hgt - 28}" rx="{(hgt - 28) / 2}"/></clipPath>', "</defs>",
        f'<rect x="-300" y="14" width="{width + 600}" height="{hgt - 28}" rx="{(hgt - 28) / 2}" fill="url(#{prefix}-vg)"/>',
        f'<g clip-path="url(#{prefix}-clip)">',
        f'<rect x="-300" y="24" width="{width + 600}" height="9" fill="#ff9a9a" opacity="0.22"/>',
        f'<rect x="-300" y="{hgt - 36}" width="{width + 600}" height="7" fill="#2a0008" opacity="0.35"/>',
    ]
    speed = (width + 500) / max(dur, 3.0)
    for i in range(n_cells):
        y = rnd.uniform(50, hgt - 50)
        x0 = rnd.uniform(-width - 200, width)
        parts.append(f'<g transform="translate({x0:.0f},{y:.0f})"><g id="{prefix}-c{i}"><g transform="rotate({rnd.uniform(-35, 35):.0f}) scale({rnd.uniform(0.8, 1.15):.2f})">'
                     f'<ellipse rx="36" ry="25" fill="url(#{prefix}-rbc)"/><ellipse rx="15" ry="9" fill="#9a1b2b" opacity="0.55"/></g></g></g>')
        tw(f'tl.fromTo("#{prefix}-c{i}", {{x:0}}, {{x:{speed * dur * rnd.uniform(0.85, 1.1):.0f}, duration:{f(dur)}, ease:"none"}}, {f(t0)});')
    for i in range(n_hex):
        y = rnd.uniform(48, hgt - 48)
        x0 = rnd.uniform(-width * 0.8, width - 80)
        r = rnd.uniform(17, 23)
        parts.append(f'<g transform="translate({x0:.0f},{y:.0f})"><g id="{prefix}-g{i}" opacity="0">'
                     f'<polygon points="{hexagon(0, 0, r)}" fill="rgba(255,200,69,0.22)" stroke="#ffc845" stroke-width="4"/><circle r="4" fill="#fff3c4"/></g></g>')
        appear = t0 + dur * (hex_from + (hex_to - hex_from) * i / max(1, n_hex - 1))
        tw(f'tl.fromTo("#{prefix}-g{i}", {{x:0, rotation:0}}, {{x:{speed * dur * 0.8:.0f}, rotation:{rnd.choice([-1, 1]) * 120}, transformOrigin:"50% 50%", duration:{f(dur)}, ease:"none"}}, {f(t0)});')
        tw(f'tl.fromTo("#{prefix}-g{i}", {{opacity:0, scale:0.2}}, {{opacity:1, scale:1, duration:0.35, ease:"back.out(2)"}}, {f(appear)});')
    parts.append("</g></svg>")
    return "".join(parts)


def _bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))


def pancreas(prefix):
    P = ((40, 120), (190, 190), (380, 70), (520, 150))
    pts = [_bez(*P, i / 140) for i in range(141)]

    def sm(t, e0, e1):
        x = min(1, max(0, (t - e0) / (e1 - e0)))
        return x * x * (3 - 2 * x)

    lobes, shade, hi = [], [], []
    for i, (x, y) in enumerate(pts):
        t = i / 140
        r = (30 + 34 * sm(t, 0.0, 0.45) - 10 * sm(t, 0.62, 0.74) + 78 * sm(t, 0.74, 0.97)) / 2 * (1 + 0.10 * math.sin(i * 1.7) + 0.06 * math.sin(i * 0.53))
        lobes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>')
        shade.append(f'<circle cx="{x + 4:.1f}" cy="{y + 9:.1f}" r="{r:.1f}"/>')
        if i % 3 == 0:
            for _ in range(2):
                ang, d = rnd.uniform(0, 6.28), rnd.uniform(0, r * 0.75)
                hi.append(f'<circle cx="{x + d * math.cos(ang):.1f}" cy="{y + d * math.sin(ang):.1f}" r="{rnd.uniform(4, 9):.1f}" fill="#fff" opacity="{rnd.uniform(0.10, 0.22):.2f}"/>')
    duct = " ".join(f"{x:.1f},{y + 4:.1f}" for x, y in pts[6:128])
    hx, hy = pts[-1]
    rr = 96
    a0, a1 = math.radians(-110), math.radians(115)
    duo = f"M {hx + rr * math.cos(a0):.1f} {hy + rr * math.sin(a0):.1f} A {rr} {rr} 0 1 1 {hx + rr * math.cos(a1):.1f} {hy + rr * math.sin(a1):.1f}"
    return (f'<svg class="pancreas" viewBox="0 0 680 300" width="680" height="300">'
            f'<defs><linearGradient id="{prefix}-pg" gradientUnits="userSpaceOnUse" x1="40" y1="60" x2="600" y2="260">'
            '<stop offset="0" stop-color="#ffcfb2"/><stop offset="0.5" stop-color="#f39a7e"/><stop offset="1" stop-color="#d0675d"/></linearGradient>'
            f'<linearGradient id="{prefix}-dg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f2b0a8"/><stop offset="1" stop-color="#b9606a"/></linearGradient></defs>'
            f'<path d="{duo}" fill="none" stroke="#7a2f3a" stroke-width="58" stroke-linecap="round" opacity="0.45" transform="translate(4,8)"/>'
            f'<path d="{duo}" fill="none" stroke="url(#{prefix}-dg)" stroke-width="52" stroke-linecap="round"/>'
            f'<path d="{duo}" fill="none" stroke="#ffd6d0" stroke-width="8" stroke-linecap="round" opacity="0.45" transform="translate(-8,-6)"/>'
            f'<g fill="#8a3a3a" opacity="0.45">{"".join(shade)}</g><g fill="url(#{prefix}-pg)">{"".join(lobes)}</g><g>{"".join(hi)}</g>'
            f'<polyline points="{duct}" fill="none" stroke="#f7dd8a" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/></svg>')


def bokeh(prefix, n=14, color="rgba(94,234,212,0.10)"):
    out = []
    for i in range(n):
        s = rnd.uniform(80, 260)
        out.append(f'<div id="{prefix}-b{i}" class="bokeh" style="left:{rnd.uniform(0, 1900 - s):.0f}px;top:{rnd.uniform(0, 1080 - s):.0f}px;'
                    f'width:{s:.0f}px;height:{s:.0f}px;background:{color}"></div>')
    return "".join(out)


def drift(prefix, n, t0, t1):
    for i in range(n):
        tw(f'tl.fromTo("#{prefix}-b{i}", {{x:0, y:0}}, {{x:{rnd.uniform(-80, 80):.0f}, y:{rnd.uniform(-120, -30):.0f}, duration:{f(t1 - t0)}, ease:"none"}}, {f(t0)});')


