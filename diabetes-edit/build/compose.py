"""Generate index.html (the HyperFrames composition) from build/edit.json.

Run: python3 build/edl.py && python3 build/compose.py

One standalone composition with one GSAP timeline. All graphics are anchored to spoken words
(see `at()`), so they follow transcript or cut changes automatically. Sound effects are listed in
build/sfx.json for the final mix (build/mix.sh); the composition itself renders picture only.
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
W, H = 1080, 1920

rnd = random.Random(42)


def norm(w):
    return re.sub(r"[^a-z0-9\-]", "", w.lower())


def at(word, after=0.0):
    """Output time of the first spoken `word` at or after `after`."""
    for w in WORDS:
        if norm(w["text"]) == word and w["start"] >= after - 1e-6:
            return round(w["start"], 3)
    raise KeyError(f"{word} after {after}")


def sec(name):
    return SECTIONS[name]["start"]


def esc(s):
    return html.escape(s, quote=True)


def f(x):
    return f"{x:.3f}"


JS = []
SFX = []
BODY = []


_SEEN = set()


def tw(line):
    """Add a tween. A later fromTo on an already-animated target must not render its
    from-values at build time, or it would overwrite the earlier resting state."""
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


def clip(ident, start, end, inner, cls="", z=10, track=1, style=""):
    BODY.append(
        f'<div id="{ident}" class="clip {cls}" data-start="{f(start)}" data-duration="{f(end - start)}" '
        f'data-track-index="{track}" style="z-index:{z};{style}">{inner}</div>'
    )


def icon(name, size, ident=None, cls=""):
    i = f' id="{ident}"' if ident else ""
    return f'<img{i} class="ico {cls}" src="assets/icons/{name}.webp" alt="" style="width:{size}px;height:{size}px" />'


# ------------------------------------------------------------------ reusable motion
def pop_in(sel, t, dur=0.45, scale=0.6, y=0):
    tw(f'tl.fromTo("{sel}", {{opacity:0, scale:{scale}, y:{y}}}, {{opacity:1, scale:1, y:0, duration:{dur}, ease:"back.out(2.2)"}}, {f(t)});')


def rise_in(sel, t, dur=0.5, y=40, stagger=0):
    st = f", stagger:{stagger}" if stagger else ""
    tw(f'tl.fromTo("{sel}", {{opacity:0, y:{y}}}, {{opacity:1, y:0, duration:{dur}, ease:"power3.out"{st}}}, {f(t)});')


def fade_out(sel, t, dur=0.3, y=-20):
    tw(f'tl.to("{sel}", {{opacity:0, y:{y}, duration:{dur}, ease:"power2.in"}}, {f(t)});')


def iris_in(sel, t, dur=0.5, cx="50%", cy="42%"):
    tw(f'tl.fromTo("{sel}", {{clipPath:"circle(0% at {cx} {cy})"}}, {{clipPath:"circle(120% at {cx} {cy})", duration:{dur}, ease:"power3.inOut"}}, {f(t)});')


def wipe_out(sel, t, dur=0.38):
    tw(f'tl.fromTo("{sel}", {{clipPath:"inset(0% 0% 0% 0%)"}}, {{clipPath:"inset(0% 0% 100% 0%)", duration:{dur}, ease:"power3.in"}}, {f(t)});')


def leak(t, strength=0.75):
    """Warm light-leak flash that hides a cut."""
    tw(f'tl.fromTo("#leak", {{opacity:0, xPercent:-12}}, {{opacity:{strength}, xPercent:0, duration:0.16, ease:"power1.out"}}, {f(t - 0.12)});')
    tw(f'tl.to("#leak", {{opacity:0, xPercent:10, duration:0.45, ease:"power1.in"}}, {f(t + 0.05)});')


def punch(t, s0=1.06):
    tw(f'tl.fromTo("#cam", {{scale:{s0}}}, {{scale:1, duration:0.55, ease:"power3.out"}}, {f(t)});')


# ------------------------------------------------------------------ anatomy kit (SVG)
def hexagon(cx, cy, r):
    pts = " ".join(f"{cx + r * math.cos(math.radians(60 * k + 30)):.1f},{cy + r * math.sin(math.radians(60 * k + 30)):.1f}" for k in range(6))
    return pts


def vessel(prefix, t0, t1, n_cells=14, n_hex=16, hex_from=0.0, hex_to=0.8, height=250, glow=True):
    """Blood vessel band (1080 wide) with flowing red cells and glucose molecules.
    Returns SVG markup; registers tweens. Glucose molecules fade in progressively between
    hex_from and hex_to (fractions of the scene) to show glucose building up."""
    dur = t1 - t0
    hgt = height
    parts = [
        f'<svg class="vessel" viewBox="0 0 1080 {hgt}" width="1080" height="{hgt}">',
        "<defs>",
        f'<linearGradient id="{prefix}-vg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#5b0d1c"/><stop offset="0.18" stop-color="#9e1f33"/>'
        '<stop offset="0.5" stop-color="#c0303f"/><stop offset="0.82" stop-color="#9e1f33"/>'
        '<stop offset="1" stop-color="#4a0a17"/></linearGradient>',
        f'<radialGradient id="{prefix}-rbc" cx="0.5" cy="0.5" r="0.5">'
        '<stop offset="0" stop-color="#a51d2d"/><stop offset="0.45" stop-color="#d23c4a"/>'
        '<stop offset="0.8" stop-color="#ef5d63"/><stop offset="1" stop-color="#b52436"/></radialGradient>',
        f'<clipPath id="{prefix}-clip"><rect x="-300" y="14" width="1680" height="{hgt - 28}" rx="{(hgt - 28) / 2}"/></clipPath>',
        "</defs>",
        f'<rect x="-300" y="14" width="1680" height="{hgt - 28}" rx="{(hgt - 28) / 2}" fill="url(#{prefix}-vg)"/>',
        f'<g clip-path="url(#{prefix}-clip)">',
        f'<rect x="-300" y="24" width="1680" height="9" fill="#ff9a9a" opacity="0.22"/>',
        f'<rect x="-300" y="{hgt - 36}" width="1680" height="7" fill="#2a0008" opacity="0.35"/>',
    ]
    speed = 1500 / max(dur, 3.0)
    for i in range(n_cells):
        y = rnd.uniform(50, hgt - 50)
        x0 = rnd.uniform(-1300, 1080)
        rot = rnd.uniform(-35, 35)
        sc = rnd.uniform(0.8, 1.15)
        parts.append(
            f'<g transform="translate({x0:.0f},{y:.0f})"><g id="{prefix}-c{i}"><g transform="rotate({rot:.0f}) scale({sc:.2f})">'
            f'<ellipse rx="36" ry="25" fill="url(#{prefix}-rbc)"/><ellipse rx="15" ry="9" fill="#9a1b2b" opacity="0.55"/></g></g></g>'
        )
        tw(f'tl.fromTo("#{prefix}-c{i}", {{x:0}}, {{x:{speed * dur * rnd.uniform(0.85, 1.1):.0f}, duration:{f(dur)}, ease:"none"}}, {f(t0)});')
    for i in range(n_hex):
        y = rnd.uniform(48, hgt - 48)
        x0 = rnd.uniform(-900, 1000)
        r = rnd.uniform(17, 23)
        parts.append(
            f'<g transform="translate({x0:.0f},{y:.0f})"><g id="{prefix}-g{i}" opacity="0">'
            f'<polygon points="{hexagon(0, 0, r)}" fill="rgba(255,200,69,0.22)" stroke="#ffc845" stroke-width="4"/>'
            f'<circle r="4" fill="#fff3c4"/></g></g>'
        )
        appear = t0 + dur * (hex_from + (hex_to - hex_from) * i / max(1, n_hex - 1))
        tw(f'tl.fromTo("#{prefix}-g{i}", {{x:0, rotation:0}}, {{x:{speed * dur * 0.8:.0f}, rotation:{rnd.choice([-1, 1]) * 120}, transformOrigin:"50% 50%", duration:{f(dur)}, ease:"none"}}, {f(t0)});')
        tw(f'tl.fromTo("#{prefix}-g{i}", {{opacity:0, scale:0.2}}, {{opacity:1, scale:1, duration:0.35, ease:"back.out(2)"}}, {f(appear)});')
    parts.append("</g></svg>")
    return "".join(parts)


def _bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))


def pancreas(prefix):
    """Lobulated pancreas (tail left, head right) cradled by the duodenal C-loop."""
    P = ((40, 120), (190, 190), (380, 70), (520, 150))
    pts = [_bez(*P, i / 140) for i in range(141)]

    def thick(t):
        sm = lambda e0, e1: min(1, max(0, (t - e0) / (e1 - e0))) ** 2 * (3 - 2 * min(1, max(0, (t - e0) / (e1 - e0))))
        return 30 + 34 * sm(0.0, 0.45) - 10 * sm(0.62, 0.74) + 78 * sm(0.74, 0.97)

    lobes, shade, hi = [], [], []
    for i, (x, y) in enumerate(pts):
        t = i / 140
        r = thick(t) / 2 * (1 + 0.10 * math.sin(i * 1.7) + 0.06 * math.sin(i * 0.53))
        lobes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>')
        shade.append(f'<circle cx="{x + 4:.1f}" cy="{y + 9:.1f}" r="{r:.1f}"/>')
        if i % 3 == 0:
            for _ in range(2):
                ang = rnd.uniform(0, 6.28)
                d = rnd.uniform(0, r * 0.75)
                hi.append(f'<circle cx="{x + d * math.cos(ang):.1f}" cy="{y + d * math.sin(ang):.1f}" r="{rnd.uniform(4, 9):.1f}" fill="#fff" opacity="{rnd.uniform(0.10, 0.22):.2f}"/>')
    duct = " ".join(f"{x:.1f},{y + 4:.1f}" for x, y in pts[6:128])
    hx, hy = pts[-1]
    rr = 96
    a0, a1 = math.radians(-110), math.radians(115)
    duo = (f"M {hx + rr * math.cos(a0):.1f} {hy + rr * math.sin(a0):.1f} "
           f"A {rr} {rr} 0 1 1 {hx + rr * math.cos(a1):.1f} {hy + rr * math.sin(a1):.1f}")
    return (
        f'<svg class="pancreas" viewBox="0 0 680 300" width="680" height="300">'
        f'<defs><linearGradient id="{prefix}-pg" gradientUnits="userSpaceOnUse" x1="40" y1="60" x2="600" y2="260">'
        '<stop offset="0" stop-color="#ffcfb2"/><stop offset="0.5" stop-color="#f39a7e"/><stop offset="1" stop-color="#d0675d"/></linearGradient>'
        f'<linearGradient id="{prefix}-dg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f2b0a8"/><stop offset="1" stop-color="#b9606a"/></linearGradient></defs>'
        f'<path d="{duo}" fill="none" stroke="#7a2f3a" stroke-width="58" stroke-linecap="round" opacity="0.45" transform="translate(4,8)"/>'
        f'<path d="{duo}" fill="none" stroke="url(#{prefix}-dg)" stroke-width="52" stroke-linecap="round"/>'
        f'<path d="{duo}" fill="none" stroke="#ffd6d0" stroke-width="8" stroke-linecap="round" opacity="0.45" transform="translate(-8,-6)"/>'
        f'<g fill="#8a3a3a" opacity="0.45">{"".join(shade)}</g>'
        f'<g fill="url(#{prefix}-pg)">{"".join(lobes)}</g>'
        f'<g>{"".join(hi)}</g>'
        f'<polyline points="{duct}" fill="none" stroke="#f7dd8a" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>'
        "</svg>"
    )


def bokeh(prefix, n=14, color="rgba(94,234,212,0.10)"):
    out = []
    for i in range(n):
        s = rnd.uniform(60, 220)
        out.append(
            f'<div id="{prefix}-b{i}" class="bokeh" style="left:{rnd.uniform(-60, 1040):.0f}px;top:{rnd.uniform(-60, 1880):.0f}px;'
            f'width:{s:.0f}px;height:{s:.0f}px;background:{color}"></div>'
        )
    return "".join(out)


def drift(prefix, n, t0, t1):
    for i in range(n):
        tw(f'tl.fromTo("#{prefix}-b{i}", {{x:0, y:0}}, {{x:{rnd.uniform(-60, 60):.0f}, y:{rnd.uniform(-140, -40):.0f}, duration:{f(t1 - t0)}, ease:"none"}}, {f(t0)});')


# ================================================================== SCENES
# ---------------------------------------------------------------- hook: 6-8 of 10 patients
Q = sec("question")
hook_end = sec("question") + 4.93
t10 = at("10")
t6 = at("6")
t78 = at("7-8")
people = "".join(
    f'<div class="pp" id="pp{i}"><div class="pp-disc" id="ppd{i}"></div>{icon("person", 74)}</div>' for i in range(10)
)
clip("hook", 0, hook_end, f"""
<div id="hook-in" class="card glass top-card">
  <div class="kicker" id="hook-k">DIABETES &middot; AYURVEDA</div>
  <div class="stat-row" id="hook-stat">
    <div class="stat-num"><span id="hook-6">6</span><span class="dash">&ndash;</span><span id="hook-8">8</span></div>
    <div class="stat-of">
      <div class="of-big">/ 10</div>
      <div class="of-small">patients diabetic</div>
    </div>
  </div>
  <div class="people" id="hook-people">{people}</div>
</div>""", z=30)
rise_in("#hook-in", 0.15, 0.6, 60)
rise_in("#hook-k", 0.35, 0.4, 16)
tw(f'tl.fromTo(".pp", {{opacity:0, y:30, scale:0.7}}, {{opacity:1, y:0, scale:1, duration:0.35, stagger:0.06, ease:"back.out(2)"}}, {f(t10 - 0.1)});')
for i in range(6):
    tw(f'tl.fromTo("#ppd{i}", {{scale:0, opacity:0}}, {{scale:1, opacity:1, duration:0.3, ease:"back.out(2.5)"}}, {f(t6 + i * 0.05)});')
for i in (6, 7):
    tw(f'tl.fromTo("#ppd{i}", {{scale:0, opacity:0}}, {{scale:1, opacity:0.6, duration:0.3, ease:"back.out(2.5)"}}, {f(t78 + (i - 6) * 0.06)});')
tw(f'tl.fromTo("#hook-stat", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.45, ease:"power3.out"}}, {f(t6 - 0.05)});')
tw(f'tl.fromTo("#hook-6", {{scale:1.6}}, {{scale:1, duration:0.4, ease:"back.out(2)"}}, {f(t6)});')
tw(f'tl.fromTo("#hook-8", {{opacity:0, scale:1.6}}, {{opacity:1, scale:1, duration:0.4, ease:"back.out(2)"}}, {f(t78)});')
fade_out("#hook-in", hook_end - 0.32, 0.3, -40)
sfx("whoosh-cinematic", 0.05, 0.35)
sfx("click-soft", t10 - 0.05, 0.35)
sfx("pop", t6, 0.4)
sfx("pop", t78, 0.35)

# ---------------------------------------------------------------- question title
q0 = hook_end
q1 = sec("charaka")
title_words = [("Diabetes", "hl"), ("ke", ""), ("patients", ""), ("itne", ""), ("kyun", "hl2"), ("badh", ""), ("rahe", ""), ("hain?", "")]
tws = "".join(f'<span class="tw-mask"><span class="tw {c}">{esc(w)}</span></span> ' for w, c in title_words)
clip("qtitle", q0, q1, f"""
<div id="qt-in" class="top-card">
  <div class="qt-row"><div class="kicker light" id="qt-k">AAJKAL &middot; APNE DESH MEIN</div>{icon("chart", 96, "qt-chart")}</div>
  <div class="q-title" id="qt-t">{tws}</div>
</div>""", z=30)
rise_in("#qt-k", q0 + 0.05, 0.4, 16)
tw(f'tl.fromTo("#qt-t .tw", {{yPercent:110}}, {{yPercent:0, duration:0.5, stagger:0.07, ease:"power4.out"}}, {f(q0 + 0.1)});')
pop_in("#qt-chart", at("badh") - 0.1, 0.5, 0.3, 20)
fade_out("#qt-in", q1 - 0.3, 0.28, -40)
sfx("whoosh-short", q0 + 0.02, 0.35)

# ---------------------------------------------------------------- doctor intro: lower third + Charaka card
c0 = sec("charaka")
c1 = sec("stress")
leak(c0, 0.8)
punch(c0, 1.07)
sfx("whoosh", c0 - 0.15, 0.45)
lt0, lt1 = c0 + 0.35, c1 - 0.05
clip("lower-third", lt0, lt1, """
<div id="lt-in" class="lt">
  <div class="lt-bar" id="lt-bar"></div>
  <div class="lt-panel" id="lt-panel">
    <div class="lt-name" id="lt-name">Dr. Mohan Padole</div>
    <div class="lt-sub" id="lt-sub">Saikrupa Ayurvedic Hospital, Nagpur</div>
  </div>
</div>""", z=35)
tw(f'tl.fromTo("#lt-bar", {{scaleY:0}}, {{scaleY:1, duration:0.35, ease:"power3.out"}}, {f(lt0)});')
tw(f'tl.fromTo("#lt-panel", {{clipPath:"inset(0% 100% 0% 0%)"}}, {{clipPath:"inset(0% 0% 0% 0%)", duration:0.55, ease:"power3.out"}}, {f(lt0 + 0.15)});')
rise_in("#lt-name", lt0 + 0.3, 0.45, 24)
rise_in("#lt-sub", lt0 + 0.42, 0.45, 18)
tw(f'tl.to("#lt-in", {{opacity:0, x:-60, duration:0.35, ease:"power2.in"}}, {f(lt1 - 0.4)});')
sfx("click-soft", lt0 + 0.1, 0.4)

ch0 = at("charakacharya") - 0.05
clip("charaka", ch0, c1, f"""
<div id="ch-in" class="top-card parchment">
  <div class="ch-row">
    {icon("scroll", 120, "ch-scroll")}
    <div class="ch-txt">
      <div class="ch-small" id="ch-small">AYURVED &middot; CHARAKACHARYA</div>
      <div class="ch-deva" id="ch-deva">&#x091A;&#x0930;&#x0915; &#x0938;&#x0902;&#x0939;&#x093F;&#x0924;&#x093E;</div>
      <div class="ch-latin" id="ch-latin">Charaka Samhita</div>
    </div>
  </div>
</div>
<div class="ch-eq" id="ch-eq"><span class="eq-a">Diabetes</span><span class="eq-sign">=</span><span class="eq-b">Madhumeh <span class="deva-s">&#x092E;&#x0927;&#x0941;&#x092E;&#x0947;&#x0939;</span></span></div>""", z=30)
rise_in("#ch-in", ch0, 0.55, 50)
pop_in("#ch-scroll", ch0 + 0.15, 0.5, 0.4)
rise_in("#ch-small", ch0 + 0.25, 0.4, 14)
rise_in("#ch-deva", ch0 + 0.32, 0.5, 20)
rise_in("#ch-latin", ch0 + 0.42, 0.45, 14)
tw(f'tl.fromTo("#ch-eq", {{opacity:0, scale:0.85}}, {{opacity:1, scale:1, duration:0.45, ease:"back.out(2)"}}, {f(at("madhumeh") - 0.05)});')
fade_out("#ch-in", c1 - 0.3, 0.28, -40)
fade_out("#ch-eq", c1 - 0.3, 0.28, -20)
sfx("sparkle", ch0 + 0.1, 0.25)
sfx("pop", at("madhumeh"), 0.3)

# ---------------------------------------------------------------- stress callout
s0 = sec("stress")
leak(s0, 0.6)
punch(s0, 1.05)
sfx("whoosh-short", s0 - 0.1, 0.35)
anat0 = at("to", s0) - 0.12
clip("stress-card", s0 + 0.05, anat0 + 0.05, f"""
<div id="sc-in" class="top-card glass tight">
  <div class="sc-row">
    <div class="sc-item" id="sc-a">{icon("anxious", 96)}<div class="sc-lbl">Chinta</div></div>
    <div class="sc-plus" id="sc-plus">+</div>
    <div class="sc-item" id="sc-b">{icon("briefcase", 96)}<div class="sc-lbl">Vyapaar</div></div>
  </div>
  <div class="stamp" id="sc-stamp">STRESS</div>
</div>""", z=30)
rise_in("#sc-in", s0 + 0.05, 0.45, 40)
pop_in("#sc-a", at("chinta"), 0.5, 0.4)
pop_in("#sc-plus", at("vyapaar") - 0.15, 0.3, 0.4)
pop_in("#sc-b", at("vyapaar"), 0.5, 0.4)
t_stress = at("stress", s0)
tw(f'tl.fromTo("#sc-stamp", {{opacity:0, scale:2.4, rotation:-14}}, {{opacity:1, scale:1, rotation:-6, duration:0.32, ease:"power4.in"}}, {f(t_stress - 0.12)});')
tw(f'tl.fromTo("#sc-in", {{x:-10}}, {{x:0, duration:0.25, ease:"elastic.out(1,0.3)"}}, {f(t_stress + 0.2)});')
sfx("pop", at("chinta"), 0.35)
sfx("pop", at("vyapaar"), 0.35)
sfx("impact-bass-1", t_stress + 0.18, 0.35)

# ---------------------------------------------------------------- anatomy B-roll: stress -> diabetes
a0, a1 = anat0, sec("dairy")
ves = vessel("av", a0, a1, n_cells=16, n_hex=18, hex_from=0.15, hex_to=0.85, height=300)
ins_dots = "".join(f'<div class="ins" id="ins{i}"></div>' for i in range(14))
clip("broll-anatomy", a0, a1, f"""
<div id="an-in" class="scene navy">
  {bokeh("anb", 12)}
  <div class="scene-title" id="an-title">
    <span class="w-coral" id="an-t1">STRESS</span>
    <span class="arrow" id="an-arr">&rarr;</span>
    <span class="w-white" id="an-t2">DIABETES</span>
  </div>
  <div class="pill gold" id="an-pill">ek mahatvapurna kaaran</div>
  <div class="an-pancreas" id="an-panc">{pancreas("ap")}</div>
  <div class="tag teal" id="an-tag-p">Pancreas</div>
  <div class="an-ins-wrap">{ins_dots}</div>
  <div class="tag teal2" id="an-tag-i"><span class="dot teal"></span>Insulin</div>
  <div class="an-vessel" id="an-ves">{ves}</div>
  <div class="tag gold" id="an-tag-g"><span class="hexi"></span>Glucose</div>
  <div class="tag coral" id="an-tag-b">Blood glucose &uarr;</div>
</div>""", z=20, track=2)
iris_in("#an-in", a0, 0.55)
drift("anb", 12, a0, a1)
rise_in("#an-t1", a0 + 0.25, 0.45, 30)
tw(f'tl.fromTo("#an-arr", {{opacity:0, x:-40}}, {{opacity:1, x:0, duration:0.4, ease:"power3.out"}}, {f(at("stress", a0) - 0.05)});')
tw(f'tl.fromTo("#an-t2", {{opacity:0, scale:0.7}}, {{opacity:1, scale:1, duration:0.45, ease:"back.out(2)"}}, {f(at("diabetes", a0) - 0.05)});')
tw(f'tl.fromTo("#an-panc", {{opacity:0, y:40, scale:0.92}}, {{opacity:1, y:0, scale:1, duration:0.7, ease:"power3.out"}}, {f(a0 + 0.3)});')
tw(f'tl.fromTo("#an-panc", {{rotation:-1.5}}, {{rotation:1.5, duration:{f(a1 - a0)}, ease:"sine.inOut"}}, {f(a0)});')
tw(f'tl.fromTo("#an-ves", {{opacity:0, y:50}}, {{opacity:1, y:0, duration:0.6, ease:"power3.out"}}, {f(a0 + 0.45)});')
pop_in("#an-tag-p", a0 + 0.9, 0.4, 0.6)
pop_in("#an-tag-i", a0 + 1.5, 0.4, 0.6)
pop_in("#an-tag-g", a0 + 2.1, 0.4, 0.6)
pop_in("#an-tag-b", at("diabetes", a0) + 0.35, 0.45, 0.6)
tw(f'tl.fromTo("#an-pill", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.45, ease:"power3.out"}}, {f(at("mahatvapurna") - 0.1)});')
for i in range(14):
    te = a0 + 0.8 + i * (a1 - a0 - 1.6) / 14
    x = 380 + (i % 5) * 70 + rnd.uniform(-20, 20)
    tw(f'tl.fromTo("#ins{i}", {{opacity:0, x:{x:.0f}, y:0, scale:0.4}}, {{opacity:1, y:90, scale:1, duration:0.35, ease:"power2.out"}}, {f(te)});')
    tw(f'tl.to("#ins{i}", {{opacity:0, y:250, x:{x + rnd.uniform(-60, 60):.0f}, duration:0.9, ease:"power1.in"}}, {f(te + 0.35)});')
wipe_out("#an-in", a1 - 0.36)
sfx("whoosh-cinematic", a0 - 0.1, 0.4)
sfx("ping", at("mahatvapurna"), 0.3)
sfx("whoosh-short", a1 - 0.3, 0.3)

# ---------------------------------------------------------------- dairy
d0 = sec("dairy")
d_br0 = at("doodh") - 0.25
clip("cow-chip", d0 + 0.05, d_br0 + 0.05, f"""
<div id="cow-in" class="chip-top">{icon("cow", 120)}<span>Gaay se utpann</span></div>""", z=30)
rise_in("#cow-in", at("gaay") - 0.15, 0.45, 30)
sfx("pop", at("gaay"), 0.35)

d_br1 = at("use", at("prayog")) - 0.12
cards = [("milk", "Doodh", "doodh"), ("bowl", "Dahi", "dahi"), ("butter", "Ghee", "ghee")]
dc = "".join(f'<div class="food-card" id="fc-{k}">{icon(i, 210)}<div class="fc-lbl">{lbl}</div></div>' for k, (i, lbl, _) in enumerate(cards))
clip("broll-dairy", d_br0, d_br1, f"""
<div id="dy-in" class="scene cream">
  {bokeh("dyb", 10, "rgba(255,200,120,0.18)")}
  <div class="scene-kicker dark" id="dy-k">GAAY SE UTPANN</div>
  <div class="food-row">{dc}</div>
  <div class="meter-wrap" id="dy-meter">
    <div class="meter-lbl"><span id="dy-ml">ZYADA PRAYOG</span>{icon("warning", 84, "dy-warn")}</div>
    <div class="meter"><div class="meter-fill" id="dy-fill"></div></div>
  </div>
  <div class="pill coral big" id="dy-res">&rarr; Diabetes</div>
</div>""", z=20, track=2)
iris_in("#dy-in", d_br0, 0.5, "50%", "40%")
drift("dyb", 10, d_br0, d_br1)
rise_in("#dy-k", d_br0 + 0.2, 0.4, 14)
for k, (_, _, word) in enumerate(cards):
    tw(f'tl.fromTo("#fc-{k}", {{opacity:0, y:80, scale:0.6, rotation:{-8 + 8 * k}}}, {{opacity:1, y:0, scale:1, rotation:0, duration:0.55, ease:"back.out(1.8)"}}, {f(at(word) - 0.1)});')
    sfx("pop", at(word), 0.4)
tz = at("zyada")
rise_in("#dy-meter", tz - 0.35, 0.4, 30)
tw(f'tl.fromTo("#dy-fill", {{scaleX:0}}, {{scaleX:1, duration:1.1, ease:"power2.inOut"}}, {f(tz - 0.1)});')
pop_in("#dy-warn", tz + 0.7, 0.45, 0.3)
tw(f'tl.to(".food-card", {{boxShadow:"0 0 0 6px rgba(255,107,107,0.85), 0 30px 60px rgba(120,40,20,0.25)", duration:0.4}}, {f(tz + 0.6)});')
tw(f'tl.fromTo("#dy-res", {{opacity:0, scale:0.7}}, {{opacity:1, scale:1, duration:0.4, ease:"back.out(2)"}}, {f(d_br1 - 0.45)});')
wipe_out("#dy-in", d_br1 - 0.36)
sfx("whoosh", d_br0 - 0.15, 0.4)
sfx("riser", tz - 0.2, 0.18)
sfx("ping", tz + 0.7, 0.3)
sfx("whoosh-short", d_br1 - 0.3, 0.3)

dd1 = sec("grain")
clip("dairy-sum", d_br1, dd1, f"""
<div id="ds-in" class="chip-top wide">{icon("milk", 92)}{icon("bowl", 92)}{icon("butter", 92)}<span class="arrow-s">&rarr;</span><span class="coral-t">Diabetes</span></div>""", z=30)
rise_in("#ds-in", at("diabetes", d_br1) - 0.15, 0.4, 24)
fade_out("#ds-in", dd1 - 0.3, 0.25)

# ---------------------------------------------------------------- grain
g0 = sec("grain")
g1 = at("kyunki") - 0.15
leak(g0, 0.65)
grain_cards = [("rice", "Naya chaawal", "chaawal", "nahi"), ("sheaf", "Naya anaaj", "anaaj", "nahi")]
gc = "".join(
    f'<div class="food-card dark" id="gc-{k}">{icon(i, 250)}<div class="fc-lbl">{lbl}</div>'
    f'<div class="xmark" id="gx-{k}">{icon("cross", 170)}</div></div>'
    for k, (i, lbl, _, _) in enumerate(grain_cards)
)
clip("broll-grain", g0, g1, f"""
<div id="gr-in" class="scene forest">
  {bokeh("grb", 10, "rgba(244,185,66,0.10)")}
  <div class="scene-title serif" id="gr-title">Naya chaawal, naya anaaj</div>
  <div class="food-row two">{gc}</div>
  <div class="pill gold" id="gr-pill">use nahi karna chahiye</div>
</div>""", z=20, track=2)
iris_in("#gr-in", g0, 0.5)
drift("grb", 10, g0, g1)
rise_in("#gr-title", g0 + 0.2, 0.5, 30)
t_nahi1 = at("nahi", g0)
t_nahi2 = at("nahi", t_nahi1 + 0.3)
for k, (_, _, word, _) in enumerate(grain_cards):
    tw(f'tl.fromTo("#gc-{k}", {{opacity:0, y:80, scale:0.6}}, {{opacity:1, y:0, scale:1, duration:0.55, ease:"back.out(1.8)"}}, {f(at(word, g0) - 0.15)});')
    sfx("pop", at(word, g0), 0.35)
for k, tt in enumerate((t_nahi1, t_nahi2)):
    tw(f'tl.fromTo("#gx-{k}", {{opacity:0, scale:2.2, rotation:-20}}, {{opacity:1, scale:1, rotation:0, duration:0.3, ease:"power4.in"}}, {f(tt - 0.05)});')
    sfx("click", tt + 0.22, 0.45)
tw(f'tl.fromTo("#gr-pill", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.4, ease:"power3.out"}}, {f(t_nahi1 + 0.2)});')
wipe_out("#gr-in", g1 - 0.36)
sfx("whoosh", g0 - 0.15, 0.4)
sfx("whoosh-short", g1 - 0.3, 0.3)

k1 = at("kaph", g1) - 0.2
clip("kapha-chip", g1, k1 + 0.05, f"""
<div id="kc-in" class="chip-top kapha"><span class="deva-big">&#x0915;&#x092B;</span><span>Kapha <b class="up">&uarr;</b></span></div>""", z=30)
pop_in("#kc-in", at("kaph-kaarak") - 0.1, 0.5, 0.6)
sfx("pop", at("kaph-kaarak"), 0.35)

k2 = sec("sweets")
ves2 = vessel("kv", k1, k2, n_cells=12, n_hex=14, hex_from=0.4, hex_to=0.95, height=260)
clip("broll-kapha", k1, k2, f"""
<div id="kp-in" class="scene navy">
  {bokeh("kpb", 10)}
  <div class="chain">
    <div class="node" id="kn0"><div class="node-ic">{icon("rice", 130)}{icon("sheaf", 130)}</div><div class="node-lbl">Naya anaaj</div></div>
    <svg class="chain-arrow" viewBox="0 0 40 120" width="40" height="120"><path id="ka0" d="M20 5 L20 100 M6 86 L20 104 L34 86" fill="none" stroke="#f4b942" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>
    <div class="node kapha" id="kn1"><div class="deva-xl">&#x0915;&#x092B;</div><div class="node-lbl">Kapha badhta <b class="up">&uarr;</b></div></div>
    <svg class="chain-arrow" viewBox="0 0 40 120" width="40" height="120"><path id="ka1" d="M20 5 L20 100 M6 86 L20 104 L34 86" fill="none" stroke="#f4b942" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>
    <div class="node diab" id="kn2"><div class="node-ic">{icon("blood", 120)}</div><div class="node-lbl">Diabetes</div></div>
  </div>
  <div class="kp-vessel" id="kp-ves">{ves2}</div>
</div>""", z=20, track=2)
iris_in("#kp-in", k1, 0.5, "50%", "30%")
drift("kpb", 10, k1, k2)
pop_in("#kn0", k1 + 0.15, 0.5, 0.6)
t_kb = at("kaph", k1)
tw(f'tl.fromTo("#ka0", {{strokeDashoffset:1}}, {{strokeDashoffset:0, duration:0.4, ease:"power2.out"}}, {f(t_kb - 0.15)});')
pop_in("#kn1", t_kb + 0.15, 0.5, 0.6)
t_kk = at("kaaran", t_kb)
tw(f'tl.fromTo("#ka1", {{strokeDashoffset:1}}, {{strokeDashoffset:0, duration:0.4, ease:"power2.out"}}, {f(t_kk - 0.2)});')
t_kd = at("diabetes", k1)
pop_in("#kn2", t_kd - 0.1, 0.5, 0.6)
tw(f'tl.fromTo("#kp-ves", {{opacity:0}}, {{opacity:0.9, duration:0.8}}, {f(k1 + 0.3)});')
wipe_out("#kp-in", k2 - 0.36)
sfx("whoosh", k1 - 0.15, 0.4)
sfx("click-soft", t_kb, 0.4)
sfx("click-soft", t_kk, 0.4)
sfx("ping", t_kd, 0.32)

# ---------------------------------------------------------------- sweets
w0 = sec("sweets")
sw_br0 = at("jaise", w0) - 0.25
clip("sweet-chip", w0 + 0.05, sw_br0 + 0.05, f"""
<div id="mc-in" class="chip-top">{icon("candy", 110)}<span>Zyada meetha</span></div>""", z=30)
pop_in("#mc-in", at("meetha", w0) - 0.15, 0.45, 0.6)
sfx("pop", at("meetha", w0), 0.35)

sw_br1 = at("jo", at("cheezein")) - 0.12
cane = (
    '<svg viewBox="0 0 160 520" width="130" height="420" class="cane">'
    '<defs><linearGradient id="cg" x1="0" x2="1"><stop offset="0" stop-color="#5f8f2f"/><stop offset="0.5" stop-color="#a7cf5a"/><stop offset="1" stop-color="#4c7a24"/></linearGradient></defs>'
    + "".join(f'<rect x="{45 + (i % 2) * 6}" y="{60 + i * 90}" width="56" height="86" rx="18" fill="url(#cg)"/><rect x="{43 + (i % 2) * 6}" y="{140 + i * 90}" width="60" height="10" rx="5" fill="#d9e8a0"/>' for i in range(5))
    + '<path d="M75 66 C 40 20, 10 10, 0 0 M78 64 C 100 10, 140 0, 160 4 M76 64 C 70 20, 80 5, 86 0" stroke="#7fb03d" stroke-width="10" fill="none" stroke-linecap="round"/>'
    "</svg>"
)
sugar = (
    '<svg viewBox="0 0 240 200" width="170" height="142" class="sugar">'
    + "".join(
        f'<g transform="translate({x},{y})"><polygon points="0,30 40,10 80,30 40,50" fill="#ffffff"/><polygon points="0,30 40,50 40,100 0,80" fill="#e6ecf2"/>'
        f'<polygon points="80,30 40,50 40,100 80,80" fill="#cfd8e2"/></g>'
        for x, y in ((20, 90), (110, 90), (65, 40))
    )
    + "</svg>"
)
gud = (
    '<svg viewBox="0 0 240 200" width="170" height="142" class="gud">'
    '<defs><linearGradient id="gg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c98a3a"/><stop offset="1" stop-color="#7a4416"/></linearGradient></defs>'
    '<path d="M40 70 L120 30 L205 62 L200 150 L120 185 L35 150 Z" fill="url(#gg)"/>'
    '<path d="M40 70 L120 104 L205 62 M120 104 L120 185" stroke="#5c3010" stroke-width="5" fill="none" opacity="0.6"/>'
    '<circle cx="90" cy="130" r="7" fill="#e1a85a" opacity="0.7"/><circle cx="160" cy="120" r="9" fill="#e1a85a" opacity="0.6"/><circle cx="150" cy="70" r="6" fill="#f3c27a" opacity="0.7"/>'
    "</svg>"
)
sweets = ["lollipop", "doughnut", "custard", "cookie", "candy"]
sw_icons = "".join(f'<div class="sweet" id="sw{i}">{icon(n, 170)}</div>' for i, n in enumerate(sweets))
clip("broll-sweets", sw_br0, sw_br1, f"""
<div id="sw-in" class="scene plum">
  {bokeh("swb", 10, "rgba(255,150,200,0.10)")}
  <div class="scene-title serif" id="sw-title">Ganne se banayi cheezein</div>
  <div class="cane-row">
    <div class="cane-wrap" id="sw-cane">{cane}<div class="fc-lbl light">Ganna</div></div>
    <div class="cane-arrows"><div class="arr-s" id="sw-a1">&rarr;</div><div class="arr-s" id="sw-a2">&rarr;</div></div>
    <div class="cane-out">
      <div class="out-card" id="sw-sugar">{sugar}<div class="fc-lbl light">Shakkar</div></div>
      <div class="out-card" id="sw-gud">{gud}<div class="fc-lbl light">Gud</div></div>
    </div>
  </div>
  <div class="sweets-row">{sw_icons}</div>
  <div class="pill pink" id="sw-pill">meethi cheezein</div>
</div>""", z=20, track=2)
iris_in("#sw-in", sw_br0, 0.5)
drift("swb", 10, sw_br0, sw_br1)
rise_in("#sw-title", sw_br0 + 0.2, 0.5, 30)
tw(f'tl.fromTo("#sw-cane", {{opacity:0, y:120}}, {{opacity:1, y:0, duration:0.6, ease:"back.out(1.5)"}}, {f(at("ganne") - 0.15)});')
tw(f'tl.fromTo("#sw-a1", {{opacity:0, x:-30}}, {{opacity:1, x:0, duration:0.3}}, {f(at("shakkar") - 0.25)});')
pop_in("#sw-sugar", at("shakkar") - 0.1, 0.5, 0.5)
tw(f'tl.fromTo("#sw-a2", {{opacity:0, x:-30}}, {{opacity:1, x:0, duration:0.3}}, {f(at("gud") - 0.25)});')
pop_in("#sw-gud", at("gud") - 0.1, 0.5, 0.5)
t_meethi = at("meethi")
tw(f'tl.fromTo(".sweet", {{opacity:0, y:120, scale:0.4, rotation:-25}}, {{opacity:1, y:0, scale:1, rotation:0, duration:0.5, stagger:0.09, ease:"back.out(2)"}}, {f(t_meethi - 0.35)});')
tw(f'tl.fromTo("#sw-pill", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.4, ease:"power3.out"}}, {f(t_meethi)});')
wipe_out("#sw-in", sw_br1 - 0.36)
sfx("whoosh", sw_br0 - 0.15, 0.4)
sfx("pop", at("ganne"), 0.35)
sfx("pop", at("shakkar"), 0.35)
sfx("pop", at("gud"), 0.35)
sfx("sparkle", t_meethi - 0.3, 0.3)
sfx("whoosh-short", sw_br1 - 0.3, 0.3)

bb0 = sw_br1
bb1 = sec("conclusion")
t_bb = at("baar-baar")
clip("baar-baar", bb0, bb1, f"""
<div id="bb-in" class="chip-top col">{icon("repeat", 92, "bb-ic")}
  <div class="bb-stamps"><span class="bb" id="bb0">BAAR</span><span class="bb" id="bb1">BAAR</span><span class="bb" id="bb2">BAAR</span></div>
</div>""", z=30)
pop_in("#bb-in", bb0 + 0.05, 0.4, 0.6)
tw(f'tl.fromTo("#bb-ic", {{rotation:0}}, {{rotation:360, duration:1.2, ease:"power2.inOut"}}, {f(t_bb - 0.2)});')
for i in range(3):
    tw(f'tl.fromTo("#bb{i}", {{opacity:0, scale:2, rotation:{-10 + i * 8}}}, {{opacity:1, scale:1, rotation:{-4 + i * 4}, duration:0.22, ease:"power4.in"}}, {f(t_bb + i * 0.2)});')
    sfx("click", t_bb + i * 0.2 + 0.15, 0.4)
fade_out("#bb-in", bb1 - 0.3, 0.25)

# ---------------------------------------------------------------- conclusion
n0 = sec("conclusion")
leak(n0, 0.6)
punch(n0, 1.05)
sfx("whoosh-short", n0 - 0.1, 0.35)
clip("conclusion", n0 + 0.05, SPEECH_END, f"""
<div id="cn-in" class="top-card glass">
  <div class="cn-line" id="cn1">{icon("couch", 84)}<span>Sabhi log <b class="gold-t">sukhi</b></span></div>
  <div class="cn-line" id="cn2">{icon("anxious", 84)}<span>Sabhi <b class="coral-t">stress</b> mein</span></div>
  <div class="cn-res" id="cn3">Yahi ek kaaran</div>
</div>""", z=30)
rise_in("#cn-in", n0 + 0.1, 0.4, 30)
tw(f'tl.fromTo("#cn1", {{opacity:0, x:-80}}, {{opacity:1, x:0, duration:0.45, ease:"power3.out"}}, {f(at("sabhi", n0) - 0.1)});')
tw(f'tl.fromTo("#cn2", {{opacity:0, x:-80}}, {{opacity:1, x:0, duration:0.45, ease:"power3.out"}}, {f(at("sabhi", at("sukhi")) - 0.1)});')
tw(f'tl.fromTo("#cn3", {{opacity:0, scale:0.7}}, {{opacity:1, scale:1, duration:0.5, ease:"back.out(2)"}}, {f(at("yahi") - 0.1)});')
sfx("pop", at("sukhi"), 0.35)
sfx("pop", at("stress", n0), 0.35)
sfx("ping", at("yahi"), 0.32)

# ---------------------------------------------------------------- end card
e0 = SPEECH_END - 0.05
recap = [("anxious", "Chinta, stress"), ("milk", "Zyada doodh, dahi, ghee"), ("rice", "Naya chaawal, naya anaaj"), ("candy", "Baar-baar meetha")]
rc = "".join(f'<div class="rc" id="rc{i}">{icon(ic, 92)}<span>{esc(t)}</span></div>' for i, (ic, t) in enumerate(recap))
clip("endcard", e0, TOTAL, f"""
<div id="ec-in" class="scene navy end">
  {bokeh("ecb", 12)}
  <div class="ec-head" id="ec-head">Diabetes ke kaaran</div>
  <div class="ec-recap">{rc}</div>
  <div class="ec-brand" id="ec-brand">
    <div class="ec-logo" id="ec-logo">{icon("herb", 120)}</div>
    <div class="ec-name" id="ec-name">Dr. Mohan Padole</div>
    <div class="ec-rule" id="ec-rule"></div>
    <div class="ec-sub" id="ec-sub">Saikrupa Ayurvedic Hospital</div>
    <div class="ec-city" id="ec-city">NAGPUR</div>
  </div>
</div>""", z=40, track=3)
iris_in("#ec-in", e0, 0.5, "50%", "35%")
drift("ecb", 12, e0, TOTAL)
rise_in("#ec-head", e0 + 0.2, 0.45, 20)
tw(f'tl.fromTo(".rc", {{opacity:0, x:-60}}, {{opacity:1, x:0, duration:0.4, stagger:0.12, ease:"power3.out"}}, {f(e0 + 0.3)});')
pop_in("#ec-logo", e0 + 0.85, 0.5, 0.4)
rise_in("#ec-name", e0 + 0.95, 0.55, 30)
tw(f'tl.fromTo("#ec-rule", {{scaleX:0}}, {{scaleX:1, duration:0.5, ease:"power3.out"}}, {f(e0 + 1.1)});')
rise_in("#ec-sub", e0 + 1.15, 0.5, 20)
rise_in("#ec-city", e0 + 1.25, 0.5, 20)
sfx("whoosh-cinematic", e0 - 0.15, 0.4)
sfx("chime", e0 + 0.9, 0.4)

# ================================================================== CAPTIONS
pages = []
cur = []
for w in WORDS:
    txt = " ".join(x["text"] for x in cur + [w])
    phrase_break = cur and (cur[-1]["text"][-1] in ".?" or w["start"] - cur[-1]["end"] > 0.35)
    if cur and (len(txt) > 21 or phrase_break or (cur[-1]["text"][-1] == "," and len(txt) > 12)):
        pages.append(cur)
        cur = []
    cur.append(w)
if cur:
    pages.append(cur)

for pi, pg in enumerate(pages):
    start = pg[0]["start"] - 0.06
    nxt = pages[pi + 1][0]["start"] - 0.06 if pi + 1 < len(pages) else SPEECH_END
    end = min(nxt, pg[-1]["end"] + 0.6) if nxt - pg[-1]["end"] > 0.6 else nxt
    end = min(end, SPEECH_END - 0.05)
    spans = []
    for wi, w in enumerate(pg):
        cls = "cw kw" if w["kw"] else "cw"
        spans.append(f'<span class="{cls}" id="cw{pi}-{wi}">{esc(w["text"])}</span>')
    clip(f"cap{pi}", start, end, f'<div class="cap" id="cap{pi}-in">{"".join(spans)}</div>', cls="cap-clip", z=60, track=5)
    tw(f'tl.fromTo("#cap{pi}-in", {{opacity:0, y:26, scale:0.96}}, {{opacity:1, y:0, scale:1, duration:0.18, ease:"power2.out"}}, {f(start)});')
    for wi, w in enumerate(pg):
        tw(f'tl.fromTo("#cw{pi}-{wi}", {{color:"{"#7ff0e0" if w["kw"] else "#ffffff"}", scale:1}}, {{color:"#ffc845", scale:1.1, duration:0.08, ease:"power1.out"}}, {f(w["start"])});')
        tw(f'tl.to("#cw{pi}-{wi}", {{color:"{"#7ff0e0" if w["kw"] else "#ffffff"}", scale:1, duration:0.12}}, {f(max(w["end"], w["start"] + 0.12))});')

# ================================================================== DOCUMENT
CSS = """
@font-face { font-family: "Fraunces"; src: url("assets/fonts/fraunces-latin-full.woff2") format("woff2"); font-weight: 100 900; }
@font-face { font-family: "Montserrat"; src: url("assets/fonts/montserrat-latin-wght.woff2") format("woff2"); font-weight: 100 900; }
@font-face { font-family: "Noto Serif Devanagari"; src: url("assets/fonts/noto-serif-devanagari-devanagari-700-normal.woff2") format("woff2"); font-weight: 700; }
:root { --navy:#07131f; --navy2:#0f2236; --teal:#2bd4c4; --teal-l:#7ff0e0; --gold:#f4b942; --gold-l:#ffc845; --coral:#ff6b6b; --cream:#fff6e6; --ink:#1d2a36; }
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1920px; overflow:hidden; background:#05101c; }
body { font-family:"Montserrat", sans-serif; color:#fff; }
#root { position:relative; width:100%; height:100%; overflow:hidden; background:#05101c; }
.clip { position:absolute; inset:0; }
#cam { position:absolute; inset:0; transform-origin:50% 40%; }
#aroll { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
.scrim-top { position:absolute; left:0; right:0; top:0; height:760px; background:linear-gradient(180deg, rgba(4,12,22,0.78) 0%, rgba(4,12,22,0.45) 45%, rgba(4,12,22,0) 100%); z-index:5; pointer-events:none; }
.scrim-bot { position:absolute; left:0; right:0; bottom:0; height:900px; background:linear-gradient(0deg, rgba(4,12,22,0.80) 0%, rgba(4,12,22,0.5) 40%, rgba(4,12,22,0) 100%); z-index:5; pointer-events:none; }
#leak { position:absolute; inset:-10%; z-index:50; opacity:0; pointer-events:none; mix-blend-mode:screen;
  background: radial-gradient(60% 45% at 30% 35%, rgba(255,190,110,0.95), rgba(255,140,60,0.35) 50%, rgba(255,120,40,0) 75%),
              radial-gradient(40% 40% at 80% 70%, rgba(255,230,180,0.8), rgba(255,200,120,0) 70%); }
.ico { display:block; object-fit:contain; filter: drop-shadow(0 14px 22px rgba(0,0,0,0.35)); }

/* cards */
.top-card { position:absolute; left:70px; right:70px; top:170px; padding:34px 44px; border-radius:40px; }
.top-card.tight { top:150px; padding:26px 40px; }
.glass { background:linear-gradient(160deg, rgba(14,34,54,0.86), rgba(7,19,31,0.80)); border:2px solid rgba(127,240,224,0.28); box-shadow:0 40px 80px rgba(0,0,0,0.45); }
.kicker { font-weight:800; font-size:30px; letter-spacing:0.22em; color:var(--gold-l); }
.kicker.light { color:var(--teal-l); }
.stat-row { display:flex; align-items:center; gap:30px; margin-top:16px; }
.stat-num { font-family:"Fraunces", serif; font-weight:800; font-size:220px; line-height:0.9; color:var(--coral); display:flex; align-items:baseline; }
.stat-num span { display:inline-block; }
.stat-num .dash { margin:0 6px; color:#ffb1a8; }
.of-big { font-family:"Fraunces", serif; font-weight:700; font-size:110px; line-height:1; }
.of-small { font-weight:700; font-size:36px; color:#cfe0ee; margin-top:8px; }
.people { display:flex; justify-content:space-between; margin-top:30px; }
.pp { position:relative; width:84px; height:84px; display:flex; align-items:center; justify-content:center; }
.pp .ico { position:relative; z-index:2; }
.pp-disc { position:absolute; inset:-4px; border-radius:50%; background:radial-gradient(circle, rgba(255,107,107,0.95), rgba(255,107,107,0.55)); box-shadow:0 0 30px rgba(255,107,107,0.8); }
.qt-row { display:flex; align-items:center; justify-content:space-between; }
.q-title { font-family:"Fraunces", serif; font-weight:800; font-size:76px; line-height:1.08; margin-top:10px; text-shadow:0 8px 30px rgba(0,0,0,0.5); }
.tw-mask { display:inline-block; overflow:hidden; vertical-align:top; padding-bottom:8px; }
.tw { display:inline-block; }
.tw.hl { color:var(--gold-l); }
.tw.hl2 { color:var(--coral); font-style:italic; }

/* lower third */
.lt { position:absolute; left:60px; top:1010px; display:flex; align-items:stretch; }
.lt-bar { width:12px; border-radius:6px; background:linear-gradient(180deg, var(--gold-l), var(--gold)); transform-origin:50% 100%; }
.lt-panel { margin-left:18px; padding:22px 34px 24px 30px; border-radius:0 26px 26px 0; background:linear-gradient(90deg, rgba(7,19,31,0.92), rgba(7,19,31,0.70)); border:1px solid rgba(255,200,69,0.25); }
.lt-name { font-family:"Fraunces", serif; font-weight:800; font-size:68px; line-height:1.05; }
.lt-sub { font-weight:700; font-size:31px; color:var(--teal-l); margin-top:8px; letter-spacing:0.01em; }

/* charaka */
.parchment { background:linear-gradient(160deg, #fbf0d9, #f1dcb2); color:#4a2b10; border:3px solid #d9b77a; box-shadow:0 40px 80px rgba(0,0,0,0.45); }
.ch-row { display:flex; align-items:center; gap:28px; }
.ch-small { font-weight:800; font-size:26px; letter-spacing:0.2em; color:#9a5b16; }
.ch-deva { font-family:"Noto Serif Devanagari", serif; font-weight:700; font-size:76px; line-height:1.25; margin-top:10px; color:#5a2e0c; }
.ch-latin { font-family:"Fraunces", serif; font-style:italic; font-weight:600; font-size:40px; color:#7a4a1c; }
.ch-eq { position:absolute; left:0; right:0; margin:0 auto; width:max-content; top:470px; display:flex; align-items:center; gap:20px; padding:14px 34px; border-radius:999px; background:rgba(7,19,31,0.88); border:2px solid rgba(255,200,69,0.4); font-weight:800; font-size:42px; }
.eq-a { color:var(--coral); } .eq-sign { color:var(--gold-l); } .eq-b { color:#fff; }
.deva-s { font-family:"Noto Serif Devanagari", serif; font-weight:700; font-size:44px; margin-left:8px; }

/* stress card */
.sc-row { display:flex; align-items:center; justify-content:center; gap:44px; }
.sc-item { display:flex; flex-direction:column; align-items:center; }
.sc-lbl { font-weight:800; font-size:42px; margin-top:8px; }
.sc-plus { font-weight:900; font-size:90px; color:var(--gold-l); }
.stamp { margin:26px auto 4px; width:max-content; padding:4px 40px; border:8px solid var(--coral); border-radius:22px; color:var(--coral); font-weight:900; font-size:84px; letter-spacing:0.1em; background:rgba(255,107,107,0.12); }

/* scenes */
.scene { position:absolute; inset:0; overflow:hidden; }
.navy { background:radial-gradient(120% 70% at 50% 30%, #13304a 0%, #0a1a2b 50%, #050d17 100%); }
.cream { background:radial-gradient(120% 70% at 50% 30%, #fffaf0 0%, #fbeacb 55%, #edd3a4 100%); color:var(--ink); }
.forest { background:radial-gradient(120% 70% at 50% 30%, #18413a 0%, #0d2622 55%, #06130f 100%); }
.plum { background:radial-gradient(120% 70% at 50% 30%, #4a1a3c 0%, #2a0f24 55%, #140712 100%); }
.bokeh { position:absolute; border-radius:50%; filter:blur(18px); }
.scene-title { position:absolute; left:0; right:0; top:200px; text-align:center; font-weight:900; font-size:80px; letter-spacing:0.02em; display:flex; justify-content:center; align-items:center; gap:18px; }
.scene-title.serif { font-family:"Fraunces", serif; font-weight:800; font-size:80px; letter-spacing:0; padding:0 60px; line-height:1.1; }
.scene-kicker { position:absolute; left:0; right:0; top:220px; text-align:center; font-weight:900; font-size:56px; letter-spacing:0.16em; }
.scene-kicker.dark { color:#8a4a12; }
.w-coral { color:var(--coral); } .w-white { color:#fff; } .arrow { color:var(--gold-l); }
.pill { position:absolute; left:0; right:0; margin:0 auto; width:max-content; padding:14px 38px; border-radius:999px; font-weight:800; font-size:44px; white-space:nowrap; }
.pill.gold { top:318px; background:rgba(255,200,69,0.16); border:3px solid var(--gold-l); color:var(--gold-l); font-family:"Fraunces", serif; font-style:italic; font-weight:700; font-size:50px; }
.pill.coral { background:var(--coral); color:#fff; }
.pill.coral.big { top:1060px; font-size:58px; padding:16px 52px; box-shadow:0 20px 40px rgba(200,60,60,0.35); }
.pill.pink { top:1125px; background:rgba(255,130,190,0.18); border:3px solid #ff9ccc; color:#ffd2e8; font-family:"Fraunces", serif; font-style:italic; }
#gr-pill { top:900px; font-size:56px; }
.an-pancreas { position:absolute; left:190px; top:420px; width:680px; height:300px; }
.an-ins-wrap { position:absolute; left:0; top:640px; width:1080px; height:300px; }
.ins { position:absolute; left:0; top:0; width:30px; height:30px; border-radius:50%; background:radial-gradient(circle at 35% 35%, #d9fffa, #2bd4c4 60%, #129c90); box-shadow:0 0 18px rgba(43,212,196,0.9); }
.an-vessel { position:absolute; left:0; top:860px; width:1080px; height:300px; }
.kp-vessel { position:absolute; left:0; top:1520px; width:1080px; height:260px; }
.tag { position:absolute; padding:10px 26px; border-radius:999px; font-weight:800; font-size:36px; display:flex; align-items:center; gap:12px; white-space:nowrap; }
.tag.teal { left:90px; top:690px; background:rgba(43,212,196,0.16); border:2px solid var(--teal); color:var(--teal-l); }
.tag.teal2 { left:690px; top:720px; background:rgba(43,212,196,0.16); border:2px solid var(--teal); color:var(--teal-l); }
.tag.gold { left:70px; top:790px; background:rgba(255,200,69,0.16); border:2px solid var(--gold-l); color:var(--gold-l); }
.tag.coral { right:70px; top:1170px; background:var(--coral); color:#fff; font-size:40px; }
.dot { width:20px; height:20px; border-radius:50%; background:var(--teal); box-shadow:0 0 12px var(--teal); }
.hexi { width:26px; height:26px; background:var(--gold-l); clip-path:polygon(25% 5%, 75% 5%, 100% 50%, 75% 95%, 25% 95%, 0 50%); }
.food-row { position:absolute; left:50px; right:50px; top:420px; display:flex; justify-content:space-between; }
.food-row.two { left:70px; right:70px; top:420px; }
.food-card { width:300px; padding:30px 10px 26px; border-radius:36px; background:#fff; box-shadow:0 30px 60px rgba(120,60,20,0.18); display:flex; flex-direction:column; align-items:center; position:relative; }
.food-card.dark { width:440px; background:linear-gradient(160deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04)); border:2px solid rgba(244,185,66,0.35); box-shadow:0 30px 60px rgba(0,0,0,0.35); }
.fc-lbl { font-weight:800; font-size:44px; margin-top:14px; color:var(--ink); }
.food-card.dark .fc-lbl, .fc-lbl.light { color:#fff; }
.xmark { position:absolute; left:0; right:0; top:56px; display:flex; justify-content:center; }
.meter-wrap { position:absolute; left:110px; right:110px; top:820px; }
.meter-lbl { display:flex; align-items:center; justify-content:space-between; font-weight:900; font-size:54px; color:#b23a2a; letter-spacing:0.06em; }
.meter { margin-top:16px; height:46px; border-radius:23px; background:rgba(60,30,10,0.12); overflow:hidden; border:3px solid rgba(120,60,20,0.15); }
.meter-fill { width:100%; height:100%; transform-origin:0 50%; background:linear-gradient(90deg, #7bd88f, #f4b942 50%, #ff6b6b); }
.chip-top { position:absolute; left:0; right:0; margin:0 auto; width:max-content; top:190px; display:flex; align-items:center; gap:24px; padding:22px 44px 22px 30px; border-radius:999px; background:linear-gradient(160deg, rgba(14,34,54,0.9), rgba(7,19,31,0.85)); border:2px solid rgba(255,200,69,0.35); font-weight:800; font-size:56px; white-space:nowrap; box-shadow:0 30px 60px rgba(0,0,0,0.45); }
.chip-top.wide { gap:12px; }
.chip-top.col { flex-direction:column; border-radius:44px; padding:24px 44px; gap:12px; top:170px; }
.chip-top.kapha { border-color:rgba(127,240,224,0.5); }
.arrow-s { color:var(--gold-l); margin:0 10px; }
.coral-t { color:var(--coral); } .gold-t { color:var(--gold-l); }
.up { color:var(--coral); }
.deva-big { font-family:"Noto Serif Devanagari", serif; font-weight:700; font-size:96px; line-height:1.2; color:var(--gold-l); }
.bb-stamps { display:flex; gap:18px; }
.bb { display:inline-block; padding:6px 22px; border:6px solid var(--coral); color:var(--coral); border-radius:16px; font-weight:900; font-size:64px; letter-spacing:0.06em; }
.chain { position:absolute; left:0; right:0; top:210px; display:flex; flex-direction:column; align-items:center; gap:10px; }
.node { min-width:560px; padding:24px 40px; border-radius:36px; background:linear-gradient(160deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04)); border:2px solid rgba(255,255,255,0.18); display:flex; flex-direction:column; align-items:center; }
.node-ic { display:flex; gap:16px; }
.node-lbl { font-weight:800; font-size:52px; margin-top:6px; }
.node.kapha { border-color:var(--teal); background:rgba(43,212,196,0.12); }
.node.diab { border-color:var(--coral); background:rgba(255,107,107,0.14); }
.deva-xl { font-family:"Noto Serif Devanagari", serif; font-weight:700; font-size:120px; line-height:1.15; color:var(--teal-l); }
.chain-arrow { display:block; }
.cane-row { position:absolute; left:80px; right:80px; top:350px; display:flex; align-items:center; justify-content:space-between; }
.cane-wrap { display:flex; flex-direction:column; align-items:center; }
.cane-arrows { display:flex; flex-direction:column; gap:130px; }
.arr-s { font-weight:900; font-size:90px; color:var(--gold-l); }
.cane-out { display:flex; flex-direction:column; gap:30px; }
.out-card { width:360px; padding:14px 20px 18px; border-radius:32px; background:linear-gradient(160deg, rgba(255,255,255,0.14), rgba(255,255,255,0.05)); border:2px solid rgba(255,180,220,0.3); display:flex; flex-direction:column; align-items:center; }
.sweets-row { position:absolute; left:60px; right:60px; top:930px; display:flex; justify-content:space-between; }
.cn-line { display:flex; align-items:center; gap:24px; font-weight:800; font-size:56px; margin:2px 0; }
.cn-res { margin-top:8px; text-align:center; font-family:"Fraunces", serif; font-weight:800; font-style:italic; font-size:66px; color:var(--gold-l); }
.end { display:flex; flex-direction:column; align-items:center; }
.ec-head { position:absolute; top:210px; left:0; right:0; text-align:center; font-weight:900; font-size:44px; letter-spacing:0.2em; color:var(--teal-l); text-transform:uppercase; }
.ec-recap { position:absolute; top:300px; left:90px; right:90px; display:flex; flex-direction:column; gap:18px; }
.rc { display:flex; align-items:center; gap:24px; padding:14px 30px; border-radius:28px; background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.12); font-weight:700; font-size:46px; }
.ec-brand { position:absolute; top:960px; left:0; right:0; display:flex; flex-direction:column; align-items:center; }
.ec-name { font-family:"Fraunces", serif; font-weight:800; font-size:112px; margin-top:16px; }
.ec-rule { width:420px; height:6px; border-radius:3px; margin:22px 0 18px; background:linear-gradient(90deg, transparent, var(--gold-l), transparent); }
.ec-sub { font-weight:800; font-size:52px; color:#fff; }
.ec-city { font-weight:800; font-size:36px; letter-spacing:0.4em; color:var(--gold-l); margin-top:14px; }

/* captions */
.cap-clip { pointer-events:none; }
.cap { position:absolute; left:50px; right:50px; top:1300px; text-align:center; font-weight:900; font-size:74px; line-height:1.18; color:#fff;
  paint-order:stroke fill; -webkit-text-stroke:12px rgba(4,12,22,0.92); text-shadow:0 10px 30px rgba(0,0,0,0.55); }
.cw { display:inline-block; margin:0 0.17em; }
.cw.kw { color:var(--teal-l); }
"""

html_doc = f"""<!doctype html>
<html lang="hi-Latn">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Diabetes: Dr. Mohan Padole</title>
    <script src="vendor/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
      <!-- generated by build/compose.py: edit the generator, then re-run it -->
      <div id="cam" data-layout-allow-overflow>
        <video id="aroll" class="clip" src="assets/video/aroll.mp4" muted playsinline data-start="0" data-duration="{f(SPEECH_END)}" data-track-index="0"></video>
      </div>
      <div class="scrim-top"></div>
      <div class="scrim-bot"></div>
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
open(os.path.join(ROOT, "index.html"), "w").write(html_doc)
json.dump(sorted(SFX, key=lambda s: s["start"]), open(os.path.join(HERE, "sfx.json"), "w"), indent=1)
print(f"wrote index.html: {len(BODY)} clips, {len(JS)} tweens, {len(pages)} caption pages, {len(SFX)} sfx")
