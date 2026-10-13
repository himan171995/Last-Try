"""Generate index.html (16:9 HyperFrames composition) from build/edit.json and build/shots.json.

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
SHOTS = json.load(open(os.path.join(HERE, "shots.json")))
WORDS = EDIT["words"]
SECTIONS = {s["name"]: s for s in EDIT["sections"]}
SPEECH_END = EDIT["speech_duration"]
END_DUR = 8.0
TOTAL = round(SPEECH_END + END_DUR, 3)
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


# ================================================================== PANEL camera moves
for i, s in enumerate(SHOTS):
    t0 = s["start"]
    t1 = SHOTS[i + 1]["start"] if i + 1 < len(SHOTS) else SPEECH_END
    origin = {"TWO": "50% 38%", "PAT_M": "55% 32%"}.get(s["shot"], "47% 33%")
    amt = 1.06 if t1 - t0 > 4 else 1.035
    tw(f'tl.fromTo("#cam", {{scale:1}}, {{scale:{amt}, transformOrigin:"{origin}", duration:{f(t1 - t0)}, ease:"sine.inOut"}}, {f(t0)});')

# ================================================================== CHAPTER TAGS
CHAPTERS = [("question", "01", "Prashn"), ("intro", "02", "Charaka Samhita"), ("sukh", "03", "Sukh aur Chinta"),
            ("stress", "04", "Stress"), ("dairy", "05", "Doodh, Dahi, Ghee"), ("grain", "06", "Naya Anaaj"),
            ("sweets", "07", "Meetha"), ("conclusion", "08", "Nishkarsh")]
for name, num, title in CHAPTERS:
    s0 = sec(name)
    s1 = sec_end(name) if name != "intro" else sec_end("shloka")
    if name == "conclusion":
        s1 = SPEECH_END
    clip(f"ch-{name}", s0, s1, f'<div class="chap" id="ch-{name}-in"><span class="chap-n">{num}</span><span class="chap-t">{esc(title)}</span></div>', "", 14, 1)
    tw(f'tl.fromTo("#ch-{name}-in", {{opacity:0, x:-40}}, {{opacity:1, x:0, duration:0.5, ease:"power3.out"}}, {f(s0 + 0.15)});')

# ================================================================== QUESTION (split)
t10, t6, t78 = at("10"), at("6"), at("7-8")
people = "".join(f'<div class="pp"><div class="pp-disc" id="ppd{i}"></div>{icon("person", 64)}</div>' for i in range(10))
q_mid = at("aajkal") - 0.25
side("q-stat", 0.2, q_mid, f"""
  <div class="kicker">DIABETES &middot; AYURVED</div>
  <div class="people" id="q-people">{people}</div>
  <div class="stat-row" id="q-statrow">
    <div class="stat-num"><span id="q-6">6</span><span class="dash">&ndash;</span><span id="q-8">8</span></div>
    <div class="stat-of"><div class="of-big">/ 10</div><div class="of-small">patients diabetic</div></div>
  </div>""")
tw(f'tl.fromTo(".pp", {{opacity:0, y:30, scale:0.7}}, {{opacity:1, y:0, scale:1, duration:0.35, stagger:0.05, ease:"back.out(2)"}}, 0.45);')
for i in range(6):
    tw(f'tl.fromTo("#ppd{i}", {{scale:0, opacity:0}}, {{scale:1, opacity:1, duration:0.3, ease:"back.out(2.5)"}}, {f(t6 + i * 0.05)});')
for i in (6, 7):
    tw(f'tl.fromTo("#ppd{i}", {{scale:0, opacity:0}}, {{scale:1, opacity:0.6, duration:0.3, ease:"back.out(2.5)"}}, {f(t78 + (i - 6) * 0.06)});')
tw(f'tl.fromTo("#q-statrow", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.45, ease:"power3.out"}}, {f(t6 - 0.05)});')
tw(f'tl.fromTo("#q-8", {{opacity:0, scale:1.6}}, {{opacity:1, scale:1, duration:0.4, ease:"back.out(2)"}}, {f(t78)});')
sfx("whoosh-cinematic", 0.05, 0.3)
sfx("pop", t6, 0.35)
sfx("pop", t78, 0.3)
qwords = [("Aajkal", ""), ("apne", ""), ("desh", ""), ("mein", ""), ("diabetes", "hl"), ("ke", ""), ("patients", ""), ("itne", ""), ("kyun", "hl2"), ("badh", ""), ("rahe", ""), ("hain?", "")]
qt = "".join(f'<span class="tw-mask"><span class="tw {c}">{esc(w)}</span></span> ' for w, c in qwords)
side("q-title", q_mid, sec_end("question") + 0.05, f'<div class="kicker teal">SAWAAL</div><div class="q-title" id="qt-t">{qt}</div>{icon("chart", 120, "qt-chart")}')
tw(f'tl.fromTo("#qt-t .tw", {{yPercent:110}}, {{yPercent:0, duration:0.45, stagger:0.06, ease:"power4.out"}}, {f(q_mid + 0.1)});')
pop_in("#qt-chart", at("badh") - 0.1, 0.5, 0.3, 20)
sfx("whoosh-short", q_mid, 0.3)

# ================================================================== TITLE (the cover)
g = EDIT["gaps"][0]
c0, c1 = g["start"], g["end"]
chips = "".join(f'<div class="cv-chip" id="cvc{i}">{icon(ic, 72)}<span>{esc(t)}</span></div>'
                for i, (ic, t) in enumerate([("anxious", "Stress"), ("milk", "Zyada doodh, dahi, ghee"), ("rice", "Naya chaawal, anaaj"), ("candy", "Baar-baar meetha")]))
full("cover", c0, c1 + 0.45, f"""
<div id="cv-in" class="scene cover">
  <img id="cv-plate" class="cv-plate" src="assets/cover/bg_plate.jpg" alt="" />
  <div class="cv-glow"></div>
  <img id="cv-doc" class="cv-doc" src="assets/cover/doc_cutout.png" alt="" />
  <div class="cv-shade"></div>
  <div class="cv-left">
    <div class="kicker" id="cv-k">AYURVED &middot; CHARAKA SAMHITA</div>
    <div class="cv-big" id="cv-big">DIABETES</div>
    <div class="cv-sub" id="cv-sub">kyun badh raha hai?</div>
    <div class="cv-chips">{chips}</div>
  </div>
  <div class="cv-brand" id="cv-brand"><div class="cv-name">Dr. Mohan Padole</div><div class="cv-hosp">Saikrupa Ayurvedic Hospital, Nagpur</div></div>
</div>""", z=40)
iris_in("#cv-in", c0, 0.6, "70%", "40%")
tw(f'tl.fromTo("#cv-plate", {{scale:1.12}}, {{scale:1.0, duration:{f(c1 - c0 + 0.45)}, ease:"none"}}, {f(c0)});')
tw(f'tl.fromTo("#cv-doc", {{opacity:0, x:120}}, {{opacity:1, x:0, duration:0.8, ease:"power3.out"}}, {f(c0 + 0.15)});')
rise_in("#cv-k", c0 + 0.3, 0.4, 16)
tw(f'tl.fromTo("#cv-big", {{opacity:0, scale:1.25}}, {{opacity:1, scale:1, duration:0.7, ease:"power4.out"}}, {f(c0 + 0.4)});')
rise_in("#cv-sub", c0 + 0.85, 0.5, 30)
tw(f'tl.fromTo(".cv-chip", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.4, stagger:0.1, ease:"power3.out"}}, {f(c0 + 1.3)});')
rise_in("#cv-brand", c0 + 1.8, 0.5, 20)
wipe_out("#cv-in", c1 - 0.05, 0.5)
sfx("impact-bass-1", c0 + 0.38, 0.45)
sfx("riser", c0 - 1.2, 0.18)
sfx("whoosh-cinematic", c1 - 0.1, 0.35)

# ================================================================== INTRO (split)
i0 = sec("intro")
leak(i0 + 0.4, 0.5)
lt0, lt1 = i0 + 0.6, at("madhumeh") + 1.2
clip("lower-third", lt0, lt1, """
<div id="lt-in" class="lt"><div class="lt-bar" id="lt-bar"></div>
  <div class="lt-panel" id="lt-panel"><div class="lt-name">Dr. Mohan Padole</div><div class="lt-sub">Saikrupa Ayurvedic Hospital, Nagpur</div></div></div>""", "", 22, 4)
tw(f'tl.fromTo("#lt-bar", {{scaleY:0}}, {{scaleY:1, duration:0.35, ease:"power3.out"}}, {f(lt0)});')
tw(f'tl.fromTo("#lt-panel", {{clipPath:"inset(0% 100% 0% 0%)"}}, {{clipPath:"inset(0% 0% 0% 0%)", duration:0.55, ease:"power3.out"}}, {f(lt0 + 0.15)});')
tw(f'tl.to("#lt-in", {{opacity:0, x:-50, duration:0.35, ease:"power2.in"}}, {f(lt1 - 0.4)});')
sfx("click-soft", lt0 + 0.1, 0.4)
i_mid = at("charakacharya", i0) - 0.2
side("i-cause", i0 + 0.1, i_mid, f'{icon("chart", 130)}<div class="big-q">Diabetes ke patient<br/>badhne ka <b class="gold-t">main kaaran?</b></div>'.replace("<br/>", " "))
side("i-charaka", i_mid, sec_end("intro") + 0.05, f"""
  <div class="parch-card"><div class="ch-row">{icon("scroll", 140)}<div>
    <div class="ch-small">AYURVED &middot; CHARAKACHARYA</div>
    <div class="ch-deva">&#x091A;&#x0930;&#x0915; &#x0938;&#x0902;&#x0939;&#x093F;&#x0924;&#x093E;</div>
    <div class="ch-latin">Charaka Samhita</div></div></div></div>
  <div class="eq" id="i-eq"><span class="coral-t">Diabetes</span><span class="gold-t">=</span><span>Madhumeh</span><span class="deva-s">&#x092E;&#x0927;&#x0941;&#x092E;&#x0947;&#x0939;</span></div>""")
pop_in("#i-eq", at("madhumeh") - 0.1, 0.45, 0.8)
sfx("sparkle", i_mid + 0.1, 0.25)
sfx("pop", at("madhumeh"), 0.3)

# ================================================================== SHLOKA (full)
sh0, sh1 = sec("shloka") - 0.15, sec_end("shloka") + 0.1
padas = [("&#x0906;&#x0938;&#x094D;&#x092F;&#x093E;&#x0938;&#x0941;&#x0916;&#x0902; &#x0938;&#x094D;&#x0935;&#x092A;&#x094D;&#x0928;&#x0938;&#x0941;&#x0916;&#x0902; &#x0926;&#x0927;&#x0940;&#x0928;&#x093F;", "aasyasukham swapnasukham dadhini", "aasya-sukham"),
         ("&#x0917;&#x094D;&#x0930;&#x093E;&#x092E;&#x094D;&#x092F;&#x094C;&#x0926;&#x0915;&#x093E;&#x0928;&#x0942;&#x092A;&#x0930;&#x0938;&#x093E;&#x0903; &#x092A;&#x092F;&#x093E;&#x0902;&#x0938;&#x093F; &#x0964;", "graamyaudakaanuparasaah payaamsi", "gramya-audaka-anupa-rasah"),
         ("&#x0928;&#x0935;&#x093E;&#x0928;&#x094D;&#x0928;&#x092A;&#x093E;&#x0928;&#x0902; &#x0917;&#x0941;&#x0921;&#x0935;&#x0948;&#x0915;&#x0943;&#x0924;&#x0902; &#x091A;", "navaannapaanam gudavaikritam cha", "navanna-panam"),
         ("&#x092A;&#x094D;&#x0930;&#x092E;&#x0947;&#x0939;&#x0939;&#x0947;&#x0924;&#x0941;&#x0903; &#x0915;&#x092B;&#x0915;&#x0943;&#x091A;&#x094D;&#x091A; &#x0938;&#x0930;&#x094D;&#x0935;&#x092E;&#x094D; &#x0965;", "pramehahetuh kaphakrichcha sarvam", "prameha-hetuh")]
plines = "".join(f'<div class="pada" id="pd{k}"><div class="pada-deva">{d}</div><div class="pada-rom">{esc(r)}</div></div>' for k, (d, r, _) in enumerate(padas))
full("shloka", sh0, sh1, f"""
<div id="sh-in" class="scene parchment-bg">
  <div class="sh-frame"></div>
  <div class="sh-head" id="sh-head">{icon("scroll", 80)}<span>Charaka Samhita</span></div>
  <div class="padas">{plines}</div>
</div>""")
iris_in("#sh-in", sh0, 0.55)
rise_in("#sh-head", sh0 + 0.2, 0.45, 20)
for k, (_, _, word) in enumerate(padas):
    tp = at(word, sh0) - 0.12
    tw(f'tl.fromTo("#pd{k}", {{opacity:0, y:24, clipPath:"inset(0% 100% 0% 0%)"}}, {{opacity:1, y:0, clipPath:"inset(0% 0% 0% 0%)", duration:0.7, ease:"power2.out"}}, {f(tp)});')
    tw(f'tl.fromTo("#pd{k} .pada-deva", {{color:"#7a3b10"}}, {{color:"#b5541a", duration:0.3}}, {f(tp)});')
    if k + 1 < len(padas):
        tw(f'tl.to("#pd{k} .pada-deva", {{color:"#5a2e0c", duration:0.4}}, {f(at(padas[k + 1][2], sh0) - 0.1)});')
wipe_out("#sh-in", sh1 - 0.4)
sfx("whoosh", sh0 - 0.1, 0.4)
sfx("chime", sh0 + 0.2, 0.25)

# ================================================================== SUKH (split)
k0 = sec("sukh")
leak(k0, 0.5)
s_b = at("charakacharya", k0) - 0.2
s_c = at("jisko", k0) - 0.25
s_d = at("aisa", s_c) + 0.4
side("s-q", k0 + 0.15, s_b, f"""
  <div class="big-q">Prameh <span class="gold-t">kisko</span> hota hai?</div>
  <div class="row2">
    <div class="mini" id="s-rais">{icon("crown", 110)}<span>Rais</span></div>
    <div class="mini" id="s-paisa">{icon("moneybag", 110)}<span>Zyada paisa</span></div>
  </div>""")
pop_in("#s-rais", at("rais") - 0.1, 0.45, 0.5)
pop_in("#s-paisa", at("paisa", k0) - 0.1, 0.45, 0.5)
side("s-sukh", s_b, s_c, f"""
  <div class="kicker">CHARAKACHARYA</div>
  <div class="row2">
    <div class="term" id="s-aasya">{icon("couch", 120)}{sanskrit("&#x0906;&#x0938;&#x094D;&#x092F;&#x093E;&#x0938;&#x0941;&#x0916;&#x0902;", "Aasya-sukham")}</div>
    <div class="term" id="s-swapna">{icon("bed", 120)}{sanskrit("&#x0938;&#x094D;&#x0935;&#x092A;&#x094D;&#x0928;&#x0938;&#x0941;&#x0916;&#x0902;", "Swapna-sukham")}</div>
  </div>
  <div class="row2 small">
    <div class="mini" id="s-p2">{icon("moneybag", 80)}<span>Paisa</span></div>
    <div class="mini" id="s-gaadi">{icon("bed", 80)}<span>Gaadi pe sona</span></div>
  </div>""")
pop_in("#s-aasya", at("aasya-sukham", s_b) - 0.1, 0.5, 0.5)
pop_in("#s-swapna", at("swapna-sukham", s_b) - 0.1, 0.5, 0.5)
pop_in("#s-p2", at("paisa", s_b) - 0.1, 0.45, 0.5)
pop_in("#s-gaadi", at("gaadi") - 0.1, 0.45, 0.5)
for wd in ("aasya-sukham", "swapna-sukham"):
    sfx("pop", at(wd, s_b), 0.3)
side("s-chinta", s_c, s_d, f"""
  <div class="row3">
    <div class="mini" id="s-ch">{icon("anxious", 120)}<span>Chinta</span></div>
    <div class="mini" id="s-vy">{icon("briefcase", 120)}<span>Vyapaar ki chinta</span></div>
  </div>
  <div class="arrow-down" id="s-arr">&darr;</div>
  <div class="result coral" id="s-res">{icon("blood", 90)}<span>Diabetes</span></div>""")
pop_in("#s-ch", at("chinta", s_c) - 0.1, 0.5, 0.5)
pop_in("#s-vy", at("vyapaar", s_c) - 0.1, 0.5, 0.5)
rise_in("#s-arr", at("usko", s_c) - 0.2, 0.3, -20)
pop_in("#s-res", at("diabetes", s_c) - 0.1, 0.5, 0.6)
sfx("pop", at("chinta", s_c), 0.3)
sfx("pop", at("vyapaar", s_c), 0.3)
sfx("ping", at("diabetes", s_c), 0.3)
side("s-ayur", s_d, sec_end("sukh") + 0.05, f"""
  {icon("herb", 150, "s-herb")}
  <div class="big-q">Ayurved mein <span class="gold-t">pehle se hi</span> sambhashan</div>""")
sfx("sparkle", at("ayurved") - 0.1, 0.25)

# ================================================================== STRESS (split, then anatomy full)
t0s = sec("stress")
leak(t0s, 0.5)
anat0 = at("to", t0s) - 0.12
t_mid = at("woh", t0s) - 0.25
side("t-eq", t0s + 0.1, t_mid, f"""
  <div class="eq big"><span class="coral-t" id="t-d">Diabetes</span><span class="gold-t" id="t-is">=</span><span id="t-c">Chinta</span></div>
  <div class="row2 c">{icon("blood", 110, "t-i1")}{icon("anxious", 110, "t-i2")}</div>""")
pop_in("#t-d", at("diabetes", t0s) - 0.1, 0.45, 0.6)
pop_in("#t-is", at("matlab", t0s) - 0.05, 0.3, 0.6)
pop_in("#t-c", at("chinta", t0s) - 0.1, 0.45, 0.6)
side("t-stress", t_mid, anat0 + 0.05, f"""
  <div class="row3">
    <div class="mini" id="t-ch">{icon("anxious", 120)}<span>Chinta</span></div>
    <div class="plus">+</div>
    <div class="mini" id="t-vy">{icon("briefcase", 120)}<span>Vyapaar</span></div>
  </div>
  <div class="stamp" id="t-stamp">STRESS</div>""")
pop_in("#t-ch", at("chinta", t_mid) - 0.1, 0.45, 0.5)
pop_in("#t-vy", at("vyapaar", t_mid) - 0.1, 0.45, 0.5)
t_st = at("stress", t_mid)
tw(f'tl.fromTo("#t-stamp", {{opacity:0, scale:2.4, rotation:-14}}, {{opacity:1, scale:1, rotation:-5, duration:0.32, ease:"power4.in"}}, {f(t_st - 0.12)});')
sfx("impact-bass-1", t_st + 0.18, 0.3)
a0, a1 = anat0, sec_end("stress") + 0.15
ves = vessel("av", a0, a1, n_cells=22, n_hex=24, hex_from=0.15, hex_to=0.85)
ins = "".join(f'<div class="ins" id="ins{i}"></div>' for i in range(14))
full("anatomy", a0, a1, f"""
<div id="an-in" class="scene navy">
  {bokeh("anb", 12)}
  <div class="scene-title" id="an-title"><span class="coral-t" id="an-t1">STRESS</span><span class="gold-t" id="an-arr">&rarr;</span><span id="an-t2">DIABETES</span></div>
  <div class="pill gold" id="an-pill">ek mahatvapurna kaaran</div>
  <div class="an-panc" id="an-panc">{pancreas("ap")}</div>
  <div class="tag teal" id="an-tp">Pancreas</div>
  <div class="an-ins">{ins}</div>
  <div class="tag teal" id="an-ti"><span class="dot"></span>Insulin</div>
  <div class="an-ves" id="an-ves">{ves}</div>
  <div class="tag gold" id="an-tg"><span class="hexi"></span>Glucose</div>
  <div class="tag coral" id="an-tb">Blood glucose &uarr;</div>
</div>""")
iris_in("#an-in", a0, 0.55)
drift("anb", 12, a0, a1)
rise_in("#an-t1", a0 + 0.2, 0.4, 30)
tw(f'tl.fromTo("#an-arr", {{opacity:0, x:-40}}, {{opacity:1, x:0, duration:0.4, ease:"power3.out"}}, {f(at("stress", a0) - 0.05)});')
pop_in("#an-t2", at("diabetes", a0) - 0.05, 0.45, 0.7)
tw(f'tl.fromTo("#an-panc", {{opacity:0, y:40, scale:0.92}}, {{opacity:1, y:0, scale:1, duration:0.7, ease:"power3.out"}}, {f(a0 + 0.3)});')
tw(f'tl.fromTo("#an-ves", {{opacity:0, y:50}}, {{opacity:1, y:0, duration:0.6, ease:"power3.out"}}, {f(a0 + 0.45)});')
pop_in("#an-tp", a0 + 0.9, 0.4, 0.6)
pop_in("#an-ti", a0 + 1.4, 0.4, 0.6)
pop_in("#an-tg", a0 + 1.9, 0.4, 0.6)
pop_in("#an-tb", at("diabetes", a0) + 0.35, 0.45, 0.6)
tw(f'tl.fromTo("#an-pill", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.45, ease:"power3.out"}}, {f(at("mahatvapurna") - 0.1)});')
for i in range(14):
    te = a0 + 0.8 + i * (a1 - a0 - 1.6) / 14
    x = 900 + (i % 5) * 60 + rnd.uniform(-20, 20)
    tw(f'tl.fromTo("#ins{i}", {{opacity:0, x:{x:.0f}, y:0, scale:0.4}}, {{opacity:1, y:70, scale:1, duration:0.35, ease:"power2.out"}}, {f(te)});')
    tw(f'tl.to("#ins{i}", {{opacity:0, y:200, x:{x + rnd.uniform(-60, 60):.0f}, duration:0.9, ease:"power1.in"}}, {f(te + 0.36)});')
wipe_out("#an-in", a1 - 0.4)
sfx("whoosh-cinematic", a0 - 0.1, 0.4)
sfx("ping", at("mahatvapurna"), 0.3)

# ================================================================== DAIRY (full, then split)
d0 = sec("dairy")
d_full0 = at("doodh", d0) - 0.3
d_full1 = at("aisa", d0) - 0.2
side("d-cow", d0 + 0.1, d_full0 + 0.05, f'<div class="row2 c">{icon("cow", 200, "d-cowi")}</div><div class="big-q c">Jo <span class="gold-t">gaay</span> se utpann</div>')
cards = [("milk", "Doodh", "doodh"), ("bowl", "Dahi", "dahi"), ("butter", "Ghee", "ghee")]
dc = "".join(f'<div class="food-card" id="fc{k}">{icon(i, 200)}<div class="fc-lbl">{lbl}</div></div>' for k, (i, lbl, _) in enumerate(cards))
full("dairy", d_full0, d_full1, f"""
<div id="dy-in" class="scene cream">
  {bokeh("dyb", 10, "rgba(255,200,120,0.20)")}
  <div class="scene-kicker" id="dy-k">GAAY SE UTPANN</div>
  <div class="food-row">{dc}</div>
  <div class="meter-wrap" id="dy-meter"><div class="meter-lbl"><span>ZYADA PRAYOG</span>{icon("warning", 80, "dy-warn")}</div>
    <div class="meter"><div class="meter-fill" id="dy-fill"></div></div></div>
  <div class="pill coral" id="dy-res">&rarr; Diabetes</div>
</div>""")
iris_in("#dy-in", d_full0, 0.5)
drift("dyb", 10, d_full0, d_full1)
rise_in("#dy-k", d_full0 + 0.2, 0.4, 14)
for k, (_, _, word) in enumerate(cards):
    tw(f'tl.fromTo("#fc{k}", {{opacity:0, y:80, scale:0.6, rotation:{-8 + 8 * k}}}, {{opacity:1, y:0, scale:1, rotation:0, duration:0.55, ease:"back.out(1.8)"}}, {f(at(word, d0) - 0.1)});')
    sfx("pop", at(word, d0), 0.4)
tz = at("zyada", d0)
rise_in("#dy-meter", tz - 0.35, 0.4, 30)
tw(f'tl.fromTo("#dy-fill", {{scaleX:0}}, {{scaleX:1, duration:1.1, ease:"power2.inOut"}}, {f(tz - 0.1)});')
pop_in("#dy-warn", tz + 0.7, 0.45, 0.3)
pop_in("#dy-res", at("diabetes", d0) - 0.1, 0.45, 0.7)
wipe_out("#dy-in", d_full1 - 0.4)
sfx("whoosh", d_full0 - 0.15, 0.4)
sfx("riser", tz - 0.2, 0.15)
sfx("ping", at("diabetes", d0), 0.3)
side("d-skt", d_full1, sec_end("dairy") + 0.05, f"""
  <div class="kicker">DOOSRA KAARAN &middot; CHARAKACHARYA</div>
  {sanskrit("&#x0917;&#x094D;&#x0930;&#x093E;&#x092E;&#x094D;&#x092F;&#x094C;&#x0926;&#x0915;&#x093E;&#x0928;&#x0942;&#x092A;&#x0930;&#x0938;&#x093E;&#x0903; &#x092A;&#x092F;&#x093E;&#x0902;&#x0938;&#x093F;", "Gramya-audaka-anupa-rasah payamsi")}
  <div class="row3">
    <div class="mini" id="d-g">{icon("cow", 110)}<span>Gaay</span></div>
    <div class="mini" id="d-b">{icon("buffalo", 110)}<span>Bhains</span></div>
    <div class="plus" id="d-arr">&rarr;</div>
    <div class="mini" id="d-p">{icon("bowl", 96)}{icon("milk", 96)}<span>Dahi, doodh</span></div>
  </div>""")
pop_in("#d-g", at("gaay", d_full1) - 0.1, 0.45, 0.5)
pop_in("#d-b", at("bhains") - 0.1, 0.45, 0.5)
pop_in("#d-arr", at("dahi", d_full1) - 0.3, 0.3, 0.5)
pop_in("#d-p", at("dahi", d_full1) - 0.1, 0.45, 0.5)
sfx("pop", at("gaay", d_full1), 0.3)
sfx("pop", at("bhains"), 0.3)

# ================================================================== GRAIN
r0 = sec("grain")
leak(r0, 0.5)
cmp0 = at("pichhle") - 0.25
cmp1 = at("kyunki") - 0.2
side("r-skt", r0 + 0.1, cmp0 + 0.05, f"""
  {sanskrit("&#x0928;&#x0935;&#x093E;&#x0928;&#x094D;&#x0928;&#x092A;&#x093E;&#x0928;&#x0902;", "Navanna-panam")}
  <div class="row2">
    <div class="mini" id="r-fasal">{icon("sheaf", 120)}<span>Nayi fasal</span></div>
    <div class="mini" id="r-anna">{icon("rice", 120)}<span>Abhi-abhi nikla anna</span></div>
  </div>""")
pop_in("#r-fasal", at("nayi", r0) - 0.1, 0.45, 0.5)
pop_in("#r-anna", at("abhi-abhi") - 0.1, 0.45, 0.5)
sfx("pop", at("nayi", r0), 0.3)
full("compare", cmp0, cmp1, f"""
<div id="cp-in" class="scene forest">
  {bokeh("cpb", 10, "rgba(244,185,66,0.10)")}
  <div class="cmp">
    <div class="cmp-card good" id="cp-a">{icon("rice", 220)}<div class="cmp-t">Puraana chaawal</div><div class="cmp-s">Pichhle saal ka</div><div class="cmp-mark" id="cp-ok">{icon("check", 120)}</div></div>
    <div class="cmp-vs">vs</div>
    <div class="cmp-card bad" id="cp-b"><div class="row2 c">{icon("rice", 180)}{icon("sheaf", 180)}</div><div class="cmp-t">Naya chaawal, naya anaaj</div><div class="cmp-s">use nahi karna chahiye</div><div class="cmp-mark" id="cp-x">{icon("cross", 130)}</div></div>
  </div>
</div>""")
iris_in("#cp-in", cmp0, 0.5)
drift("cpb", 10, cmp0, cmp1)
pop_in("#cp-a", at("pichhle") - 0.05, 0.55, 0.6)
pop_in("#cp-ok", at("use", at("puraane")) - 0.1, 0.4, 2.0)
pop_in("#cp-b", at("naye", cmp0) - 0.1, 0.55, 0.6)
tw(f'tl.fromTo("#cp-x", {{opacity:0, scale:2.2, rotation:-20}}, {{opacity:1, scale:1, rotation:0, duration:0.3, ease:"power4.in"}}, {f(at("nahi", cmp0) - 0.05)});')
sfx("whoosh", cmp0 - 0.15, 0.4)
sfx("ping", at("use", at("puraane")), 0.3)
sfx("click", at("nahi", cmp0) + 0.22, 0.45)
wipe_out("#cp-in", cmp1 - 0.4)
kp0 = at("kaph", cmp1) - 0.25
side("r-kapha", cmp1, kp0 + 0.05, f'<div class="row2 c"><div class="deva-xl">&#x0915;&#x092B;</div></div><div class="big-q c">Kaph-<span class="teal-t">kaarak</span></div>')
sfx("pop", at("kaph-kaarak") - 0.05, 0.3)
kp1 = end_of("hai", at("diabetes", kp0)) + 0.35
ves2 = vessel("kv", kp0, kp1, n_cells=16, n_hex=18, hex_from=0.45, hex_to=0.95, height=220)
full("kapha", kp0, kp1, f"""
<div id="kp-in" class="scene navy">
  {bokeh("kpb", 10)}
  <div class="chain">
    <div class="node" id="kn0"><div class="row2 c">{icon("rice", 110)}{icon("sheaf", 110)}</div><div class="node-l">Naya anaaj</div></div>
    <div class="chain-arr" id="ka0">&rarr;</div>
    <div class="node kap" id="kn1"><div class="deva-xl">&#x0915;&#x092B;</div><div class="node-l">Kaph badhta <b class="coral-t">&uarr;</b></div></div>
    <div class="chain-arr" id="ka1">&rarr;</div>
    <div class="node dia" id="kn2"><div class="row2 c">{icon("blood", 110)}</div><div class="node-l">Diabetes</div></div>
  </div>
  <div class="kp-ves" id="kp-ves">{ves2}</div>
</div>""")
iris_in("#kp-in", kp0, 0.5)
drift("kpb", 10, kp0, kp1)
pop_in("#kn0", kp0 + 0.15, 0.5, 0.6)
tb = at("kaph", kp0)
slide_in("#ka0", tb - 0.1, 0.35, -30)
pop_in("#kn1", tb + 0.1, 0.5, 0.6)
tk = at("kaaran", tb)
slide_in("#ka1", tk - 0.2, 0.35, -30)
td = at("diabetes", kp0)
pop_in("#kn2", td - 0.1, 0.5, 0.6)
tw(f'tl.fromTo("#kp-ves", {{opacity:0}}, {{opacity:0.95, duration:0.8}}, {f(kp0 + 0.3)});')
wipe_out("#kp-in", kp1 - 0.4)
sfx("whoosh", kp0 - 0.15, 0.4)
sfx("click-soft", tb, 0.4)
sfx("click-soft", tk, 0.4)
sfx("ping", td, 0.32)
side("r-samh", kp1, sec_end("grain") + 0.05, f'{icon("scroll", 150)}<div class="big-q">Is prakar se sambhashan <span class="gold-t">Charakacharya ji</span> ne bataya hai</div>')

# ================================================================== SWEETS
w0 = sec("sweets")
leak(w0, 0.5)
sw0 = at("jaise", w0) - 0.25
sw1 = at("jo", at("cheezein")) - 0.15
side("w-skt", w0 + 0.1, sw0 + 0.05, f"""
  {sanskrit("&#x0917;&#x0941;&#x0921;&#x0935;&#x0948;&#x0915;&#x0943;&#x0924;&#x0902; &#x091A;", "Guda-vaikritam cha")}
  <div class="row2 c"><div class="mini" id="w-m">{icon("candy", 130)}<span>Zyada meetha</span></div></div>""")
pop_in("#w-m", at("meetha", w0) - 0.1, 0.45, 0.5)
sfx("pop", at("meetha", w0), 0.3)
cane = ('<svg viewBox="0 0 160 520" width="120" height="390"><defs><linearGradient id="cg" x1="0" x2="1"><stop offset="0" stop-color="#5f8f2f"/><stop offset="0.5" stop-color="#a7cf5a"/><stop offset="1" stop-color="#4c7a24"/></linearGradient></defs>'
        + "".join(f'<rect x="{45 + (i % 2) * 6}" y="{60 + i * 90}" width="56" height="86" rx="18" fill="url(#cg)"/><rect x="{43 + (i % 2) * 6}" y="{140 + i * 90}" width="60" height="10" rx="5" fill="#d9e8a0"/>' for i in range(5))
        + '<path d="M75 66 C 40 20, 10 10, 0 0 M78 64 C 100 10, 140 0, 160 4 M76 64 C 70 20, 80 5, 86 0" stroke="#7fb03d" stroke-width="10" fill="none" stroke-linecap="round"/></svg>')
sugar = ('<svg viewBox="0 0 240 200" width="190" height="158">' + "".join(
    f'<g transform="translate({x},{y})"><polygon points="0,30 40,10 80,30 40,50" fill="#ffffff"/><polygon points="0,30 40,50 40,100 0,80" fill="#e6ecf2"/><polygon points="80,30 40,50 40,100 80,80" fill="#cfd8e2"/></g>'
    for x, y in ((20, 90), (110, 90), (65, 40))) + "</svg>")
gud = ('<svg viewBox="0 0 240 200" width="190" height="158"><defs><linearGradient id="gg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c98a3a"/><stop offset="1" stop-color="#7a4416"/></linearGradient></defs>'
       '<path d="M40 70 L120 30 L205 62 L200 150 L120 185 L35 150 Z" fill="url(#gg)"/><path d="M40 70 L120 104 L205 62 M120 104 L120 185" stroke="#5c3010" stroke-width="5" fill="none" opacity="0.6"/>'
       '<circle cx="90" cy="130" r="7" fill="#e1a85a" opacity="0.7"/><circle cx="160" cy="120" r="9" fill="#e1a85a" opacity="0.6"/></svg>')
sweets = "".join(f'<div class="sweet">{icon(n, 150)}</div>' for n in ["lollipop", "doughnut", "custard", "cookie", "candy"])
full("sweets", sw0, sw1, f"""
<div id="sw-in" class="scene plum">
  {bokeh("swb", 10, "rgba(255,150,200,0.10)")}
  <div class="sw-row">
    <div class="sw-col" id="sw-cane">{cane}<div class="fc-lbl light">Ganna</div></div>
    <div class="arr-s" id="sw-a1">&rarr;</div>
    <div class="out-card" id="sw-sugar">{sugar}<div class="fc-lbl light">Shakkar</div></div>
    <div class="out-card" id="sw-gud">{gud}<div class="fc-lbl light">Gud</div></div>
    <div class="arr-s" id="sw-a2">&rarr;</div>
    <div class="sweets-grid">{sweets}<div class="pill pink" id="sw-pill">meethi cheezein</div></div>
  </div>
</div>""")
iris_in("#sw-in", sw0, 0.5)
drift("swb", 10, sw0, sw1)
tw(f'tl.fromTo("#sw-cane", {{opacity:0, y:120}}, {{opacity:1, y:0, duration:0.6, ease:"back.out(1.5)"}}, {f(at("ganne") - 0.15)});')
slide_in("#sw-a1", at("shakkar") - 0.3, 0.3, -30)
pop_in("#sw-sugar", at("shakkar") - 0.1, 0.5, 0.5)
pop_in("#sw-gud", at("gud", w0) - 0.1, 0.5, 0.5)
slide_in("#sw-a2", at("inse") - 0.2, 0.3, -30)
tw(f'tl.fromTo(".sweet", {{opacity:0, y:100, scale:0.4, rotation:-25}}, {{opacity:1, y:0, scale:1, rotation:0, duration:0.5, stagger:0.08, ease:"back.out(2)"}}, {f(at("meethi") - 0.4)});')
rise_in("#sw-pill", at("meethi"), 0.4, 20)
wipe_out("#sw-in", sw1 - 0.4)
sfx("whoosh", sw0 - 0.15, 0.4)
for wd in ("ganne", "shakkar", "gud"):
    sfx("pop", at(wd, w0), 0.33)
sfx("sparkle", at("meethi") - 0.3, 0.3)
tbb = at("baar-baar")
side("w-baar", sw1, sec_end("sweets") + 0.05, f"""
  <div class="row2 c">{icon("repeat", 130, "w-rep")}</div>
  <div class="bb-row"><span class="bb" id="bb0">BAAR</span><span class="bb" id="bb1">BAAR</span><span class="bb" id="bb2">BAAR</span></div>""")
tw(f'tl.fromTo("#w-rep", {{rotation:0}}, {{rotation:360, duration:1.2, ease:"power2.inOut"}}, {f(tbb - 0.2)});')
for i in range(3):
    tw(f'tl.fromTo("#bb{i}", {{opacity:0, scale:2}}, {{opacity:1, scale:1, rotation:{-4 + i * 4}, duration:0.22, ease:"power4.in"}}, {f(tbb + i * 0.18)});')
    sfx("click", tbb + i * 0.18 + 0.15, 0.4)

# ================================================================== CONCLUSION (split)
n0 = sec("conclusion")
leak(n0, 0.5)
n_b = at("aaj") - 0.25
n_c = at("iska", n_b) - 0.2
side("n-pehle", n0 + 0.1, n_b, f"""
  <div class="parch-card"><div class="ch-row">{icon("scroll", 130)}<div>
    <div class="ch-small">CHARAKACHARYA &middot; PEHLE SE HI</div>
    <div class="ch-latin big">Kisko diabetes ho sakta hai</div></div></div></div>
  <div class="pill-inline gold" id="n-sak">bahut sakhol bataya hai</div>""")
pop_in("#n-sak", at("sakhol") - 0.1, 0.45, 0.7)
steps = [("anxious", "Stress", "stress"), ("moneybag", "Zyada paisa", "paisa"), ("couch", "Zyada sukh", "sukh"), ("blood", "Diabetes", "diabetes")]
st_html = "".join(f'<div class="step" id="ns{k}">{icon(ic, 76)}<span>{t}</span></div>' + ('<div class="step-arr" id="na{0}">&darr;</div>'.format(k) if k < 3 else "") for k, (ic, t, _) in enumerate(steps))
side("n-chain", n_b, n_c, f'<div class="kicker">AAJ BHI</div><div class="steps">{st_html}</div>')
for k, (_, _, wd) in enumerate(steps):
    tk_ = at(wd, n_b)
    pop_in(f"#ns{k}", tk_ - 0.1, 0.45, 0.5)
    if k:
        slide_in(f"#na{k - 1}", tk_ - 0.3, 0.3, -20)
    sfx("pop", tk_, 0.3)
side("n-final", n_c, SPEECH_END, f"""
  <div class="cn-line" id="nf1">{icon("couch", 96)}<span>Sabhi log <b class="gold-t">sukhi</b></span></div>
  <div class="cn-line" id="nf2">{icon("anxious", 96)}<span>Sabhi <b class="coral-t">stress</b> mein</span></div>
  <div class="cn-res" id="nf3">Yahi ek kaaran</div>""")
slide_in("#nf1", at("sabhi", n_c) - 0.1, 0.45, -60)
slide_in("#nf2", at("sabhi", at("sukhi", n_c)) - 0.1, 0.45, -60)
pop_in("#nf3", at("yahi") - 0.1, 0.5, 0.7)
sfx("pop", at("sukhi", n_c), 0.3)
sfx("pop", at("stress", at("sukhi", n_c)), 0.3)
sfx("ping", at("yahi"), 0.3)

# ================================================================== END SCREEN (full)
e0 = SPEECH_END - 0.05
recap = [("anxious", "Sukh aur chinta, stress"), ("milk", "Zyada doodh, dahi, ghee"), ("rice", "Naya chaawal, naya anaaj"), ("candy", "Baar-baar meetha")]
rc = "".join(f'<div class="rc" id="rc{i}">{icon(ic, 80)}<span>{esc(t)}</span></div>' for i, (ic, t) in enumerate(recap))
full("endscreen", e0, TOTAL, f"""
<div id="ec-in" class="scene navy">
  {bokeh("ecb", 14)}
  <img class="ec-doc" id="ec-doc" src="assets/cover/doc_cutout.png" alt="" />
  <div class="ec-left">
    <div class="kicker teal" id="ec-k">CHARAKA SAMHITA KE ANUSAAR</div>
    <div class="ec-head" id="ec-h">Diabetes ke kaaran</div>
    <div class="ec-recap">{rc}</div>
  </div>
  <div class="ec-brand" id="ec-brand">{icon("herb", 80)}<div><div class="ec-name">Dr. Mohan Padole</div><div class="ec-sub">Saikrupa Ayurvedic Hospital, Nagpur</div></div></div>
</div>""", z=45)
iris_in("#ec-in", e0, 0.6)
drift("ecb", 14, e0, TOTAL)
tw(f'tl.fromTo("#ec-doc", {{opacity:0, x:80}}, {{opacity:1, x:0, duration:0.8, ease:"power3.out"}}, {f(e0 + 0.2)});')
rise_in("#ec-k", e0 + 0.3, 0.4, 16)
rise_in("#ec-h", e0 + 0.4, 0.5, 24)
tw(f'tl.fromTo(".rc", {{opacity:0, x:-60}}, {{opacity:1, x:0, duration:0.45, stagger:0.15, ease:"power3.out"}}, {f(e0 + 0.7)});')
rise_in("#ec-brand", e0 + 1.4, 0.5, 20)
sfx("whoosh-cinematic", e0 - 0.15, 0.4)
sfx("chime", e0 + 1.3, 0.35)

# ================================================================== CAPTIONS
cuts = sorted({round(a, 3) for a, b in FULL} | {round(b, 3) for a, b in FULL})


def in_full(t):
    return any(a - 0.05 <= t < b - 0.2 for a, b in FULL)


pages, cur = [], []
for w in WORDS:
    txt = " ".join(x["text"] for x in cur + [w])
    crosses = cur and any(cur[0]["start"] < c <= w["start"] for c in cuts)
    brk = cur and (cur[-1]["text"][-1] in ".?:" or w["start"] - cur[-1]["end"] > 0.35)
    if cur and (len(txt) > 34 or brk or crosses or (cur[-1]["text"][-1] == "," and len(txt) > 20)):
        pages.append(cur)
        cur = []
    cur.append(w)
pages.append(cur)
for pi, pg in enumerate(pages):
    start = pg[0]["start"] - 0.06
    nxt = pages[pi + 1][0]["start"] - 0.06 if pi + 1 < len(pages) else SPEECH_END
    end = min(nxt, pg[-1]["end"] + 0.6) if nxt - pg[-1]["end"] > 0.6 else nxt
    end = min(end, SPEECH_END - 0.05)
    mode = "full" if in_full(pg[0]["start"]) else "side"
    spans = "".join(f'<span class="cw{" kw" if w["kw"] else ""}" id="cw{pi}-{wi}">{esc(w["text"])}</span>' for wi, w in enumerate(pg))
    clip(f"cap{pi}", start, end, f'<div class="cap {mode}" id="cap{pi}-in">{spans}</div>', "cap-clip", 60, 5)
    tw(f'tl.fromTo("#cap{pi}-in", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.16, ease:"power2.out"}}, {f(start)});')
    for wi, w in enumerate(pg):
        base = "#7ff0e0" if w["kw"] else "#ffffff"
        tw(f'tl.fromTo("#cw{pi}-{wi}", {{color:"{base}"}}, {{color:"#ffc845", duration:0.08}}, {f(w["start"])});')
        tw(f'tl.to("#cw{pi}-{wi}", {{color:"{base}", duration:0.12}}, {f(max(w["end"], w["start"] + 0.12))});')

# ================================================================== DOCUMENT
BG = bokeh("bgb", 16)
drift("bgb", 16, 0, TOTAL)
CSS = open(os.path.join(HERE, "style.css")).read()
doc = f"""<!doctype html>
<html lang="hi-Latn">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>Diabetes: Dr. Mohan Padole</title>
    <script src="vendor/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
      <!-- generated by build/compose.py: edit the generator, then re-run it -->
      <div id="bg">{BG}</div>
      <div id="panel" data-layout-allow-overflow>
        <div id="cam" data-layout-allow-overflow>
          <video id="aroll" class="clip" src="assets/video/aroll.mp4" muted playsinline data-start="0" data-duration="{f(SPEECH_END)}" data-track-index="0"></video>
        </div>
        <div class="panel-shade"></div>
      </div>
      {"".join(BODY)}
      <div id="leak" data-layout-ignore></div>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + j for j in JS)}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open(os.path.join(ROOT, "index.html"), "w").write(doc)
json.dump(sorted(SFX, key=lambda s: s["start"]), open(os.path.join(HERE, "sfx.json"), "w"), indent=1)
json.dump({"total": TOTAL, "chapters": [{"t": 0 if n == "question" else sec(n), "title": t} for n, _, t in CHAPTERS]},
          open(os.path.join(HERE, "meta.json"), "w"), indent=1)
print(f"wrote index.html: {len(BODY)} clips, {len(JS)} tweens, {len(pages)} caption pages, {len(SFX)} sfx, total {TOTAL}s")
