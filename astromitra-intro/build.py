"""Generate the ASTROMITRA RADHAA channel intro (1920x1080, ~26 s).

index.html holds the shared night sky, scene hosts and audio; each scene is a sub-composition in
compositions/ with scene-local timing. (The 6.3 s sting is build_short.py.)

Run: python3 build.py && python3 -I ../tools/make_intro_sting.py music-cues.json assets/audio/intro-sting.wav
     npx hyperframes check
"""

import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
GRID = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]  # Lo Shu: every row, column and diagonal sums to 15

# Scene windows on the main timeline (start, end); neighbours overlap for cross-fades.
SCENES = {
    "hook": (0.0, 3.7),
    "dob-grid": (3.5, 10.7),
    "services": (10.5, 16.9),
    "promise": (16.7, 19.9),
    "lockup": (19.7, 26.4),
}
TOTAL = SCENES["lockup"][1]

# Sample date of birth used to demonstrate a Lo Shu grid. Digits: 1 5 0 8 1 9 9 5.
DOB = "15081995"
MISSING = [n for n in range(1, 10) if str(n) not in DOB]  # [2, 3, 4, 6, 7]
MULANK = 6  # day 15 -> 1+5
BHAGYANK = 2  # 1+5+0+8+1+9+9+5 = 38 -> 11 -> 2

FONTS = """
      @font-face { font-family: "Cinzel"; src: url("../assets/fonts/cinzel-latin-600-normal.woff2") format("woff2"); font-weight: 600; }
      @font-face { font-family: "Cinzel"; src: url("../assets/fonts/cinzel-latin-700-normal.woff2") format("woff2"); font-weight: 700; }
      @font-face { font-family: "Montserrat"; src: url("../assets/fonts/montserrat-latin-wght.woff2") format("woff2"); font-weight: 100 900; }"""

SHARED = """
      .kicker { display: inline-block; font: 700 22px/1 "Montserrat"; letter-spacing: 0.24em; text-transform: uppercase;
        color: #f3d98b; padding: 10px 18px; border: 2px solid #e07a1f; border-radius: 999px; }
      .title { font: 700 72px/1.05 "Cinzel"; color: #f3d98b; letter-spacing: 0.02em; }
      .ico { display: block; object-fit: contain; }"""

GL_CSS = """
      svg { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: visible; }
      .gl { fill: none; stroke: #d4a84b; stroke-dasharray: 1; stroke-dashoffset: 1; stroke-linecap: round; }"""


def icon(name, size, ident=None, cls="ico"):
    i = f' id="{ident}"' if ident else ""
    return f'<img{i} class="{cls}" src="../assets/icons/{name}.webp" alt="" style="width:{size}px;height:{size}px" />'


def cell_center(n, cx, cy, cell):
    for r, row in enumerate(GRID):
        if n in row:
            return cx + (row.index(n) - 1) * cell, cy + (r - 1) * cell
    raise ValueError(n)


def grid_svg(prefix, cx, cy, cell, stroke=3):
    h = cell * 1.5
    x0, x1, y0, y1 = cx - h, cx + h, cy - h, cy + h
    out = [f'<rect id="{prefix}-frame" x="{x0}" y="{y0}" width="{2 * h}" height="{2 * h}" rx="6" class="gl" pathLength="1" style="stroke-width:{stroke}" />']
    for k, v in enumerate((cx - cell / 2, cx + cell / 2)):
        out.append(f'<line id="{prefix}-v{k}" x1="{v}" y1="{y0}" x2="{v}" y2="{y1}" class="gl" pathLength="1" style="stroke-width:{stroke}" />')
    for k, v in enumerate((cy - cell / 2, cy + cell / 2)):
        out.append(f'<line id="{prefix}-h{k}" x1="{x0}" y1="{v}" x2="{x1}" y2="{v}" class="gl" pathLength="1" style="stroke-width:{stroke}" />')
    return out


def draw_grid_js(prefix, t, dur=0.5):
    js = [f'tl.fromTo("#{prefix}-frame", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: {dur}, ease: "power2.inOut"}}, {t:.2f});']
    for k, el in enumerate(["v0", "v1", "h0", "h1"]):
        js.append(f'tl.fromTo("#{prefix}-{el}", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 0.4, ease: "power2.out"}}, {t + 0.15 + 0.07 * k:.2f});')
    return js


# ------------------------------------------------------------------ scenes (local time)
def scene_hook():
    d = SCENES["hook"][1] - SCENES["hook"][0]
    words = "What do your numbers say?".split()
    spans = "".join(f'<span class="hw" id="hw-{i}">{w}</span>' for i, w in enumerate(words))
    html = f"""<div id="hook-wrap" class="wrap">
        <div id="hook-spark"></div>
        <div id="hook-lines">
          <div id="hook-kicker" class="kicker">Astro Numerology</div>
          <div id="hook-q">{spans}</div>
          <div id="hook-sub">Your date of birth holds a map.</div>
        </div>
      </div>"""
    css = """
      .wrap { position: absolute; inset: 0; }
      #hook-spark { position: absolute; left: 900px; top: 220px; width: 120px; height: 120px; border-radius: 50%;
        background: radial-gradient(closest-side, #fff6dc, rgba(243, 217, 139, 0.7) 30%, rgba(224, 122, 31, 0) 100%); }
      #hook-lines { position: absolute; left: 0; right: 0; top: 360px; display: flex; flex-direction: column; align-items: center; }
      #hook-q { display: flex; gap: 26px; margin-top: 34px; font: 700 104px/1.1 "Cinzel"; color: #f3d98b; white-space: nowrap; }
      .hw { display: inline-block; }
      #hook-sub { margin-top: 30px; font: 600 40px/1.2 "Montserrat"; color: #f6ead3; letter-spacing: 0.04em; }"""
    js = [
        'tl.fromTo("#hook-spark", {scale: 0, opacity: 0}, {scale: 1, opacity: 1, duration: 0.4, ease: "expo.out"}, 0.05);',
        'tl.to("#hook-spark", {scale: 3, opacity: 0, duration: 0.6, ease: "power2.in"}, 0.45);',
        'tl.fromTo("#hook-kicker", {y: 16, opacity: 0}, {y: 0, opacity: 1, duration: 0.4, ease: "power3.out"}, 0.3);',
        'tl.fromTo(".hw", {y: 60, opacity: 0, rotationX: -70}, {y: 0, opacity: 1, rotationX: 0, duration: 0.6, stagger: 0.12, ease: "back.out(1.6)"}, 0.45);',
        'tl.fromTo("#hook-sub", {y: 24, opacity: 0}, {y: 0, opacity: 1, duration: 0.5, ease: "power3.out"}, 1.5);',
        f'tl.to("#hook-wrap", {{opacity: 0, y: -40, duration: 0.35, ease: "power2.in"}}, {d - 0.4:.2f});',
    ]
    sfx = [("whoosh-short", 0.3, 0.35)]
    music = [{"type": "bell", "t": 0.45, "level": 0.5, "note": 0}] + [
        {"type": "pluck", "t": 0.47 + 0.12 * i, "level": 0.35, "note": n} for i, n in enumerate([0, 2, 4, 7, 9])]
    return html, css, js, sfx, music


def scene_dob():
    d = SCENES["dob-grid"][1] - SCENES["dob-grid"][0]
    cx, cy, cell = 1270, 560, 168
    # Date-of-birth digits laid out absolutely so every flight path is known.
    groups = [DOB[:2], DOB[2:4], DOB[4:]]
    x, y = 250, 470
    slots, seps = [], []
    for gi, g in enumerate(groups):
        for ch in g:
            slots.append((ch, x))
            x += 52
        if gi < 2:
            seps.append(x + 4)
            x += 44
    digit_html = [f'<div class="dd" id="dd-{i}" style="left:{xx}px;top:{y}px">{ch}</div>' for i, (ch, xx) in enumerate(slots)]
    digit_html += [f'<div class="dsep" style="left:{xx}px;top:{y}px">-</div>' for xx in seps]
    counts = {}
    for ch in DOB:
        if ch != "0":
            counts[ch] = counts.get(ch, 0) + 1
    seen, flights, fly_html, fly_js = {}, [], [], []
    t = 1.35
    for i, (ch, xx) in enumerate(slots):
        if ch == "0":
            fly_js.append(f'tl.to("#dd-{i}", {{opacity: 0.4, y: 14, duration: 0.3, ease: "power2.in"}}, {t:.2f});')
            fly_js.append(f'tl.fromTo("#zero-note", {{opacity: 0, x: -10}}, {{opacity: 1, x: 0, duration: 0.3}}, {t:.2f});')
            t += 0.3
            continue
        n = int(ch)
        k = seen.get(ch, 0)
        seen[ch] = k + 1
        tx, ty = cell_center(n, cx, cy, cell)
        if counts[ch] == 2:
            tx += -28 if k == 0 else 28
        fid = f"fly-{i}"
        fly_html.append(f'<div class="fly" id="{fid}" style="left:{tx - 40}px;top:{ty - 50}px">{ch}</div>')
        dx, dy = (xx + 26) - tx, (y + 50) - ty
        fly_js.append(f'tl.fromTo("#{fid}", {{x: {dx:.0f}, y: {dy:.0f}, opacity: 0}}, {{x: 0, y: 0, opacity: 1, duration: 0.5, ease: "power3.inOut"}}, {t:.2f});')
        fly_js.append(f'tl.to("#dd-{i}", {{opacity: 0.55, duration: 0.25}}, {t:.2f});')
        fly_js.append(f'tl.fromTo("#cellflash-{n}-{k}", {{opacity: 0.85}}, {{opacity: 0, duration: 0.5, ease: "power2.out", immediateRender: false}}, {t + 0.45:.2f});')
        flights.append(t + 0.45)
        t += 0.42
    t_missing = t + 0.25
    ghost, flash, miss = [], [], []
    for n in range(1, 10):
        gx, gy = cell_center(n, cx, cy, cell)
        ghost.append(f'<div class="ghostnum" style="left:{gx - cell / 2 + 10}px;top:{gy - cell / 2 + 8}px">{n}</div>')
        for k in range(counts.get(str(n), 0)):
            flash.append(f'<div class="cellflash" id="cellflash-{n}-{k}" style="left:{gx - cell / 2 + 4}px;top:{gy - cell / 2 + 4}px;width:{cell - 8}px;height:{cell - 8}px"></div>')
        if n in MISSING:
            miss.append(f'<div class="miss" id="miss-{n}" style="left:{gx - cell / 2 + 12}px;top:{gy - cell / 2 + 42}px;width:{cell - 24}px;height:{cell - 54}px"><span>missing</span></div>')
    html = f"""<div id="dob-wrap" class="wrap">
        <div id="dob-head"><div id="dob-kicker" class="kicker">Lo Shu Grid</div>
          <div id="dob-title" class="title">Your birth date, mapped</div></div>
        <div id="dob-card">{icon("cake", 92, "dob-cake")}<div class="dob-label">Date of birth</div><div class="dob-eg">example</div></div>
        {"".join(digit_html)}
        <div id="zero-note">0 has no cell</div>
        <svg viewBox="0 0 1920 1080" aria-hidden="true">{"".join(grid_svg("dg", cx, cy, cell))}</svg>
        {"".join(ghost)}{"".join(flash)}{"".join(miss)}{"".join(fly_html)}
        <div id="dob-chips">
          <div class="chip" id="chip-missing">Missing: {" · ".join(str(m) for m in MISSING)}</div>
          <div class="chip chip-gold" id="chip-remedy">{icon("diya", 44)}<span>Lo Shu remedies</span></div>
        </div>
        <div id="dob-nums">
          <div class="num-pill" id="pill-mulank"><b>{MULANK}</b><span>Mulank · Driver</span></div>
          <div class="num-pill" id="pill-bhagyank"><b>{BHAGYANK}</b><span>Bhagyank · Conductor</span></div>
        </div>
      </div>"""
    css = GL_CSS + """
      .wrap { position: absolute; inset: 0; }
      #dob-head { position: absolute; left: 140px; top: 96px; }
      #dob-title { margin-top: 18px; }
      #dob-card { position: absolute; left: 200px; top: 300px; width: 640px; height: 330px; border-radius: 28px;
        background: rgba(11, 16, 51, 0.72); border: 2px solid rgba(212, 168, 75, 0.7); }
      #dob-cake { position: absolute; left: 40px; top: 36px; }
      .dob-label { position: absolute; left: 150px; top: 50px; font: 700 34px/1 "Montserrat"; color: #f6ead3; letter-spacing: 0.06em; }
      .dob-eg { position: absolute; left: 150px; top: 96px; font: 600 24px/1 "Montserrat"; color: #d4a84b; letter-spacing: 0.18em; text-transform: uppercase; }
      .dd, .dsep { position: absolute; width: 52px; height: 100px; display: flex; align-items: center; justify-content: center;
        font: 700 80px/1 "Cinzel"; color: #f6ead3; }
      .dsep { width: 40px; color: #e07a1f; }
      #zero-note { position: absolute; left: 290px; top: 586px; font: 600 24px/1 "Montserrat"; color: #e9b77a; letter-spacing: 0.06em; opacity: 0; }
      .ghostnum { position: absolute; font: 700 26px/1 "Montserrat"; color: rgba(243, 217, 139, 0.7); }
      .cellflash { position: absolute; border-radius: 10px; background: rgba(243, 217, 139, 0.35); opacity: 0; }
      .miss { position: absolute; border-radius: 14px; border: 3px dashed #e07a1f; background: rgba(224, 122, 31, 0.14);
        display: flex; align-items: center; justify-content: center; opacity: 0; }
      .miss span { font: 700 22px/1 "Montserrat"; letter-spacing: 0.12em; text-transform: uppercase; color: #f0a35a; }
      .fly { position: absolute; width: 80px; height: 100px; display: flex; align-items: center; justify-content: center;
        font: 700 76px/1 "Cinzel"; color: #f3d98b; text-shadow: 0 0 16px rgba(212, 168, 75, 0.5); }
      #dob-chips { position: absolute; left: 200px; top: 668px; display: flex; flex-direction: column; gap: 18px; align-items: flex-start; }
      .chip { display: flex; align-items: center; gap: 12px; padding: 14px 24px; border-radius: 999px; background: #5a0f1e;
        border: 2px solid #e07a1f; font: 700 32px/1 "Montserrat"; color: #f6ead3; letter-spacing: 0.04em; }
      .chip-gold { background: #f3d98b; border-color: #f3d98b; color: #1b1440; }
      #dob-nums { position: absolute; left: 200px; top: 860px; display: flex; gap: 22px; }
      .num-pill { display: flex; align-items: center; gap: 14px; padding: 10px 22px 10px 12px; border-radius: 18px;
        background: rgba(11, 16, 51, 0.8); border: 2px solid rgba(212, 168, 75, 0.7); }
      .num-pill b { width: 58px; height: 58px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        background: #d4a84b; color: #0b1033; font: 700 36px/1 "Cinzel"; }
      .num-pill span { font: 700 26px/1 "Montserrat"; color: #f6ead3; letter-spacing: 0.04em; }"""
    js = [
        'tl.fromTo("#dob-wrap", {opacity: 0}, {opacity: 1, duration: 0.3}, 0);',
        'tl.fromTo("#dob-kicker", {y: 16, opacity: 0}, {y: 0, opacity: 1, duration: 0.4, ease: "power3.out"}, 0.1);',
        'tl.fromTo("#dob-title", {y: 36, opacity: 0}, {y: 0, opacity: 1, duration: 0.55, ease: "expo.out"}, 0.2);',
        'tl.fromTo("#dob-card", {x: -60, opacity: 0}, {x: 0, opacity: 1, duration: 0.5, ease: "power3.out"}, 0.35);',
        'tl.fromTo("#dob-cake", {scale: 0.3, rotation: -20}, {scale: 1, rotation: 0, duration: 0.6, ease: "back.out(2.4)"}, 0.5);',
        'tl.fromTo(".dd, .dsep", {y: 30, opacity: 0}, {y: 0, opacity: 1, duration: 0.4, stagger: 0.04, ease: "power3.out"}, 0.6);',
        'tl.fromTo(".ghostnum", {opacity: 0}, {opacity: 1, duration: 0.5, stagger: 0.03}, 0.9);',
    ] + draw_grid_js("dg", 0.45) + fly_js
    for j, n in enumerate(MISSING):
        js.append(f'tl.fromTo("#miss-{n}", {{opacity: 0, scale: 0.8}}, {{opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)"}}, {t_missing + 0.08 * j:.2f});')
    js += [
        f'tl.fromTo("#chip-missing", {{x: -40, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.45, ease: "power3.out"}}, {t_missing + 0.3:.2f});',
        f'tl.fromTo("#chip-remedy", {{x: -40, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.45, ease: "power3.out"}}, {t_missing + 0.75:.2f});',
        f'tl.fromTo("#pill-mulank", {{y: 30, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.4, ease: "back.out(1.8)"}}, {t_missing + 1.1:.2f});',
        f'tl.fromTo("#pill-bhagyank", {{y: 30, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.4, ease: "back.out(1.8)"}}, {t_missing + 1.25:.2f});',
        f'tl.to("#dob-wrap", {{opacity: 0, duration: 0.35, ease: "power2.in"}}, {d - 0.4:.2f});',
    ]
    sfx = [("whoosh-short", 0.3, 0.3), ("ping", t_missing, 0.25), ("pop", t_missing + 0.75, 0.35)]
    bhupali = [0, 2, 4, 7, 9, 12, 14]
    music = [{"type": "pluck", "t": ft, "level": 0.38, "note": bhupali[k % len(bhupali)]} for k, ft in enumerate(flights)]
    music += [{"type": "bell", "t": t_missing, "level": 0.45, "note": 7}, {"type": "shimmer", "t": t_missing + 0.7, "level": 0.3}]
    return html, css, js, sfx, music


def scene_services():
    d = SCENES["services"][1] - SCENES["services"][0]
    cards = [
        ("numbers", "Astro Numerology", "Your numbers, decoded"),
        ("diya", "Lo Shu Grid Remedy", "Balance your grid"),
        ("crystal-ball", "Future Forecasting", "Plan for what is ahead"),
        ("compass", "Life Management", "Clarity for everyday life"),
    ]
    body = "".join(
        f'<div class="svc" id="svc-{i}"><div class="svc-disc">{icon(ic, 150, f"svc-ico-{i}")}</div>'
        f'<div class="svc-num">0{i + 1}</div><div class="svc-title">{t}</div><div class="svc-sub">{s}</div></div>'
        for i, (ic, t, s) in enumerate(cards)
    )
    html = f"""<div id="svc-wrap" class="wrap">
        <div id="svc-head"><div id="svc-kicker" class="kicker">On this channel</div>
          <div id="svc-title" class="title">Guidance, written in numbers</div></div>
        <div id="svc-row">{body}</div>
      </div>"""
    css = """
      .wrap { position: absolute; inset: 0; }
      #svc-head { position: absolute; left: 0; right: 0; top: 110px; display: flex; flex-direction: column; align-items: center; }
      #svc-title { margin-top: 20px; }
      #svc-row { position: absolute; left: 120px; right: 120px; top: 360px; display: flex; gap: 40px; }
      .svc { flex: 1; height: 520px; border-radius: 32px; padding: 40px 30px; display: flex; flex-direction: column; align-items: center;
        background: linear-gradient(180deg, rgba(24, 32, 90, 0.85), rgba(11, 16, 51, 0.85)); border: 2px solid rgba(212, 168, 75, 0.75);
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.35); }
      .svc-disc { width: 200px; height: 200px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        background: radial-gradient(closest-side, rgba(243, 217, 139, 0.28), rgba(243, 217, 139, 0.04)); border: 2px solid rgba(212, 168, 75, 0.5); }
      .svc-num { margin-top: 30px; font: 700 24px/1 "Montserrat"; letter-spacing: 0.2em; color: #e07a1f; }
      .svc-title { margin-top: 14px; font: 700 38px/1.15 "Cinzel"; color: #f3d98b; text-align: center; }
      .svc-sub { margin-top: 16px; font: 600 26px/1.3 "Montserrat"; color: #f6ead3; text-align: center; }"""
    js = [
        'tl.fromTo("#svc-wrap", {opacity: 0}, {opacity: 1, duration: 0.3}, 0);',
        'tl.fromTo("#svc-kicker", {y: 16, opacity: 0}, {y: 0, opacity: 1, duration: 0.4, ease: "power3.out"}, 0.15);',
        'tl.fromTo("#svc-title", {y: 36, opacity: 0}, {y: 0, opacity: 1, duration: 0.55, ease: "expo.out"}, 0.25);',
    ]
    sfx = [("whoosh-short", 0.2, 0.3)]
    music = []
    for i in range(4):
        t = 0.8 + 1.05 * i
        js.append(f'tl.fromTo("#svc-{i}", {{y: 90, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.6, ease: "power3.out"}}, {t:.2f});')
        js.append(f'tl.fromTo("#svc-ico-{i}", {{scale: 0.3, rotation: -25}}, {{scale: 1, rotation: 0, duration: 0.65, ease: "back.out(2.4)"}}, {t + 0.12:.2f});')
        sfx.append(("pop", t + 0.05, 0.32))
        music.append({"type": "pluck", "t": t + 0.1, "level": 0.42, "note": [0, 4, 7, 12][i]})
    js.append(f'tl.to("#svc-wrap", {{opacity: 0, duration: 0.35, ease: "power2.in"}}, {d - 0.4:.2f});')
    return html, css, js, sfx, music


def scene_promise():
    d = SCENES["promise"][1] - SCENES["promise"][0]
    cx, cy, cell = 960, 540, 230
    nums = []
    for n in range(1, 10):
        x, y = cell_center(n, cx, cy, cell)
        nums.append(f'<div class="pg-n" style="left:{x - 60}px;top:{y - 60}px">{n}</div>')
    html = f"""<div id="pr-wrap" class="wrap">
        <div id="pr-ghost"><svg viewBox="0 0 1920 1080" aria-hidden="true">{"".join(grid_svg("pg", cx, cy, cell, 2))}</svg>{"".join(nums)}</div>
        <div id="pr-lines">
          <div id="pr-a">Know your numbers.</div>
          <div id="pr-rule"></div>
          <div id="pr-b">Manage your life.</div>
        </div>
      </div>"""
    css = GL_CSS + """
      .wrap { position: absolute; inset: 0; }
      #pr-ghost { position: absolute; inset: 0; opacity: 0.12; transform-origin: 960px 540px; }
      #pr-ghost .pg-n { display: none; }
      #pr-ghost .gl { stroke-dashoffset: 0; }
      .pg-n { position: absolute; width: 120px; height: 120px; display: flex; align-items: center; justify-content: center;
        font: 700 110px/1 "Cinzel"; color: #d4a84b; }
      #pr-lines { position: absolute; left: 0; right: 0; top: 330px; display: flex; flex-direction: column; align-items: center; }
      #pr-a, #pr-b { font: 700 110px/1.1 "Cinzel"; color: #f3d98b; white-space: nowrap; }
      #pr-b { color: #f6ead3; }
      #pr-rule { width: 520px; height: 4px; margin: 34px 0; border-radius: 2px;
        background: linear-gradient(90deg, rgba(224, 122, 31, 0), #e07a1f 25%, #f3d98b 50%, #e07a1f 75%, rgba(224, 122, 31, 0)); }"""
    js = [
        'tl.fromTo("#pr-wrap", {opacity: 0}, {opacity: 1, duration: 0.3}, 0);',
        f'tl.fromTo("#pr-ghost", {{scale: 1.15}}, {{scale: 1.0, duration: {d:.2f}, ease: "none"}}, 0);',
        'tl.fromTo("#pr-a", {y: 50, opacity: 0}, {y: 0, opacity: 1, duration: 0.7, ease: "expo.out"}, 0.2);',
        'tl.fromTo("#pr-rule", {scaleX: 0}, {scaleX: 1, duration: 0.6, ease: "power3.out"}, 0.75);',
        'tl.fromTo("#pr-b", {y: 50, opacity: 0}, {y: 0, opacity: 1, duration: 0.7, ease: "expo.out"}, 1.0);',
        f'tl.to("#pr-lines", {{opacity: 0, scale: 1.04, duration: 0.4, ease: "power2.in"}}, {d - 0.45:.2f});',
        f'tl.to("#pr-ghost", {{opacity: 0, duration: 0.4, ease: "power2.in"}}, {d - 0.45:.2f});',
    ]
    sfx = [("sparkle", 1.0, 0.25)]
    music = [{"type": "bell", "t": 0.2, "level": 0.4, "note": 4}, {"type": "bell", "t": 1.0, "level": 0.45, "note": 7},
             {"type": "shimmer", "t": 1.0, "level": 0.35}]
    return html, css, js, sfx, music


def scene_lockup():
    d = SCENES["lockup"][1] - SCENES["lockup"][0]
    cx, cy, cell = 960, 450, 150
    order = [(5, 0.55), (9, 0.68), (1, 0.77), (3, 0.86), (7, 0.95), (4, 1.07), (6, 1.15), (2, 1.23), (8, 1.31)]
    t_trace, t_ring, t_shrink, t_word = 1.5, 2.15, 2.4, 2.85
    h = cell * 1.5
    x0, x1, y0, y1 = cx - h, cx + h, cy - h, cy + h
    ext = 34
    segs = [((x0 - ext, cy + (r - 1) * cell), (x1 + ext, cy + (r - 1) * cell), (x1 + 78, cy + (r - 1) * cell)) for r in range(3)]
    segs += [((cx + (c - 1) * cell, y0 - ext), (cx + (c - 1) * cell, y1 + ext), (cx + (c - 1) * cell, y1 + 70)) for c in range(3)]
    segs += [((x0 - ext, y0 - ext), (x1 + ext, y1 + ext), (x1 + 66, y1 + 62)), ((x1 + ext, y0 - ext), (x0 - ext, y1 + ext), (x0 - 66, y1 + 62))]
    svg = grid_svg("lk", cx, cy, cell)
    tags = []
    for i, ((ax, ay), (bx, by), (tx, ty)) in enumerate(segs):
        svg.append(f'<line id="tr-{i}" x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" class="trace" pathLength="1" />')
        tags.append(f'<div id="tag-{i}" class="tag" style="left:{tx - 30}px;top:{ty - 20}px">15</div>')
    svg += [f'<circle id="ring" cx="{cx}" cy="{cy}" r="322" class="ring" pathLength="1" />',
            f'<circle id="ring-in" cx="{cx}" cy="{cy}" r="300" class="ring-in" pathLength="1" />']
    for k in range(9):
        a = math.radians(-90 + 40 * k)
        svg.append(f'<circle id="dot-{k}" cx="{cx + 322 * math.cos(a):.1f}" cy="{cy + 322 * math.sin(a):.1f}" r="11" class="dot" />')
    nums = []
    for n in range(1, 10):
        x, y = cell_center(n, cx, cy, cell)
        cls = "num num-center" if n == 5 else ("num num-odd" if n % 2 else "num num-even")
        nums.append(f'<div id="lk-n-{n}" class="{cls}" style="left:{x - 60}px;top:{y - 60}px">{n}</div>')
    chars = "".join('<span class="sp"></span>' if c == " " else f'<span class="ch">{c}</span>' for c in "ASTROMITRA RADHAA")
    html = f"""<div id="lk-wrap" class="wrap">
        <div id="seal">
          <div id="halo"></div>
          <svg viewBox="0 0 1920 1080" aria-hidden="true">{"".join(svg)}</svg>
          {"".join(nums)}{"".join(tags)}
        </div>
        <div id="flash"></div>
        <div id="lk-lock">
          <div id="word-wrap"><div id="word" aria-label="ASTROMITRA RADHAA">{chars}</div><div id="glint"></div></div>
          <div id="rule"></div>
          <div id="services">Astro Numerology &#183; Lo Shu Grid Remedy &#183; Future Forecasting &#183; Life Management</div>
          <div id="sub-row">
            <div id="sub-btn"><span class="play"></span>Subscribe</div>
            <div id="bell-wrap">{icon("bell", 84, "bell")}</div>
          </div>
        </div>
      </div>"""
    css = GL_CSS + """
      .wrap { position: absolute; inset: 0; }
      #seal { position: absolute; inset: 0; transform-origin: 960px 450px; }
      .trace { fill: none; stroke: #f3d98b; stroke-width: 4; stroke-dasharray: 1; stroke-dashoffset: 1; stroke-linecap: round; opacity: 0.85; }
      .ring { fill: none; stroke: #d4a84b; stroke-width: 3; stroke-dasharray: 1; stroke-dashoffset: 1; }
      .ring-in { fill: none; stroke: #d4a84b; stroke-width: 1.5; stroke-dasharray: 1; stroke-dashoffset: 1; opacity: 0.45; }
      .dot { fill: #e07a1f; stroke: #f3d98b; stroke-width: 2; }
      #halo { position: absolute; left: 860px; top: 350px; width: 200px; height: 200px; border-radius: 50%;
        background: radial-gradient(closest-side, rgba(243, 217, 139, 0.42), rgba(243, 217, 139, 0)); }
      .num { position: absolute; width: 120px; height: 120px; display: flex; align-items: center; justify-content: center;
        font: 700 86px/1 "Cinzel"; text-shadow: 0 0 18px rgba(212, 168, 75, 0.45); }
      .num-center { color: #f3d98b; }
      .num-odd { color: #f6ead3; }
      .num-even { color: #d4a84b; }
      .tag { position: absolute; width: 60px; height: 40px; border-radius: 20px; display: flex; align-items: center; justify-content: center;
        background: #5a0f1e; border: 2px solid #e07a1f; color: #f6ead3; font: 800 22px/1 "Montserrat"; }
      #flash { position: absolute; left: 560px; top: 420px; width: 800px; height: 420px; border-radius: 50%;
        background: radial-gradient(closest-side, rgba(255, 240, 200, 0.28), rgba(243, 217, 139, 0)); }
      #lk-lock { position: absolute; left: 0; right: 0; top: 548px; display: flex; flex-direction: column; align-items: center; }
      #word-wrap { position: relative; padding: 6px 30px; }
      #word { display: flex; gap: 8px; font: 700 112px/1.05 "Cinzel"; white-space: nowrap; filter: drop-shadow(0 4px 18px rgba(212, 168, 75, 0.35)); }
      .ch { display: inline-block; color: #f3d98b; background: linear-gradient(180deg, #fbe7a8 0%, #f3d98b 35%, #d4a84b 70%, #a87b2e 100%);
        -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
      .sp { display: inline-block; width: 38px; }
      #glint { position: absolute; right: 10px; top: -14px; width: 70px; height: 70px;
        background: radial-gradient(closest-side, #fffaf0, rgba(243, 217, 139, 0.6) 25%, rgba(243, 217, 139, 0) 70%),
          linear-gradient(0deg, rgba(0,0,0,0) 46%, #fff6dc 50%, rgba(0,0,0,0) 54%),
          linear-gradient(90deg, rgba(0,0,0,0) 46%, #fff6dc 50%, rgba(0,0,0,0) 54%); }
      #rule { width: 760px; height: 3px; margin-top: 14px; background: linear-gradient(90deg, rgba(224, 122, 31, 0), #e07a1f 20%, #f3d98b 50%, #e07a1f 80%, rgba(224, 122, 31, 0)); }
      #services { margin-top: 22px; font: 600 25px/1 "Montserrat"; letter-spacing: 0.16em; color: #f6ead3; text-transform: uppercase; }
      #sub-row { margin-top: 36px; display: flex; align-items: center; gap: 26px; }
      #sub-btn { display: flex; align-items: center; gap: 16px; padding: 18px 40px; border-radius: 16px; background: #c4161c;
        font: 800 38px/1 "Montserrat"; letter-spacing: 0.06em; color: #ffffff; text-transform: uppercase; box-shadow: 0 16px 40px rgba(196, 22, 28, 0.35); }
      .play { width: 0; height: 0; border-left: 26px solid #ffffff; border-top: 16px solid transparent; border-bottom: 16px solid transparent; }
      #bell-wrap { width: 96px; height: 96px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        background: rgba(11, 16, 51, 0.85); border: 2px solid #d4a84b; }
      #bell { transform-origin: 50% 10%; }"""
    js = ['tl.fromTo("#lk-wrap", {opacity: 0}, {opacity: 1, duration: 0.3}, 0);'] + draw_grid_js("lk", 0.1)
    for n, t in order:
        js.append(f'tl.fromTo("#lk-n-{n}", {{scale: 1.8, opacity: 0, y: -10}}, {{scale: 1, opacity: 1, y: 0, duration: 0.4, ease: "back.out(2.2)"}}, {t});')
    js.append('tl.fromTo("#halo", {scale: 0.3, opacity: 0}, {scale: 1, opacity: 1, duration: 0.6, ease: "power2.out"}, 0.55);')
    for i in range(8):
        t = t_trace + 0.06 * i
        js.append(f'tl.fromTo("#tr-{i}", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 0.3, ease: "power2.out"}}, {t:.2f});')
        js.append(f'tl.fromTo("#tag-{i}", {{scale: 0, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.28, ease: "back.out(2.6)"}}, {t + 0.18:.2f});')
    js += [
        f'tl.to(".trace", {{opacity: 0, duration: 0.3}}, {t_ring:.2f});',
        f'tl.to(".tag", {{scale: 0.4, opacity: 0, duration: 0.28, ease: "power2.in"}}, {t_ring:.2f});',
        f'tl.fromTo("#ring", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 0.55, ease: "power2.inOut"}}, {t_ring:.2f});',
        f'tl.fromTo("#ring-in", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 0.55, ease: "power2.inOut"}}, {t_ring + 0.08:.2f});',
        f'tl.fromTo(".dot", {{scale: 0, transformOrigin: "50% 50%"}}, {{scale: 1, duration: 0.32, stagger: 0.035, ease: "back.out(3)"}}, {t_ring + 0.1:.2f});',
        f'tl.to("#seal", {{scale: 0.48, y: -150, duration: 0.6, ease: "power3.inOut"}}, {t_shrink:.2f});',
        f'tl.fromTo("#flash", {{opacity: 0, scale: 0.6}}, {{opacity: 1, scale: 1.4, duration: 0.18, ease: "power2.out"}}, {t_word - 0.05:.2f});',
        f'tl.to("#flash", {{opacity: 0, duration: 0.6, ease: "power2.in"}}, {t_word + 0.15:.2f});',
        f'tl.fromTo(".ch", {{opacity: 0, y: 46, scale: 1.25}}, {{opacity: 1, y: 0, scale: 1, duration: 0.55, stagger: {{each: 0.035, from: "center"}}, ease: "expo.out"}}, {t_word - 0.12:.2f});',
        f'tl.fromTo("#rule", {{scaleX: 0}}, {{scaleX: 1, duration: 0.5, ease: "power3.out"}}, {t_word + 0.4:.2f});',
        f'tl.fromTo("#services", {{opacity: 0, y: 18}}, {{opacity: 1, y: 0, duration: 0.45, ease: "power3.out"}}, {t_word + 0.55:.2f});',
        f'tl.fromTo("#sub-btn", {{scale: 0.5, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.5, ease: "back.out(2.4)"}}, {t_word + 0.95:.2f});',
        f'tl.fromTo("#bell-wrap", {{scale: 0.5, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.5, ease: "back.out(2.4)"}}, {t_word + 1.1:.2f});',
        f'tl.to("#sub-btn", {{scale: 0.94, duration: 0.09, yoyo: true, repeat: 1, ease: "power1.inOut"}}, {t_word + 1.65:.2f});',
        f'tl.fromTo("#bell", {{rotation: 0}}, {{rotation: 18, duration: 0.08, yoyo: true, repeat: 7, ease: "sine.inOut"}}, {t_word + 1.9:.2f});',
        f'tl.fromTo("#glint", {{scale: 0, rotation: -45, opacity: 0}}, {{scale: 1, rotation: 0, opacity: 1, duration: 0.35, ease: "back.out(2)"}}, {t_word + 1.2:.2f});',
        f'tl.to("#glint", {{scale: 0.2, rotation: 45, opacity: 0, duration: 0.45, ease: "power2.in"}}, {t_word + 1.57:.2f});',
    ]
    bh = [0, 2, 4, 7, 9, 12, 14, 16, 19]
    music = [{"type": "pluck", "t": t + 0.02, "level": 0.4, "note": bh[k]} for k, (_, t) in enumerate(order)]
    music += [{"type": "impact", "t": t_word, "level": 0.95}, {"type": "bell", "t": t_word, "level": 0.85, "note": 0},
              {"type": "shimmer", "t": t_trace, "level": 0.3}, {"type": "bell", "t": t_word + 1.2, "level": 0.35, "note": 7}]
    sfx = [("whoosh-cinematic", t_shrink - 0.25, 0.35), ("sparkle", t_word + 1.2, 0.3), ("pop", t_word + 1.65, 0.4),
           ("notification", t_word + 1.9, 0.35)]
    return html, css, js, sfx, music, (t_trace, t_word)


# ------------------------------------------------------------------ assembly
SFX_DUR = {"whoosh-short": 0.57, "whoosh-cinematic": 5.54, "ping": 1.32, "sparkle": 1.8, "pop": 0.72, "notification": 2.46}
SFX_LEAD = {"whoosh-short": 0.16, "whoosh-cinematic": 0.0, "ping": 0.32, "sparkle": 0.03, "pop": 0.11, "notification": 0.0}


def write_scene(ident, html, css, js, dur):
    doc = f"""<!doctype html>
<html lang="en">
  <head><meta charset="UTF-8" /><!-- generated by build.py --></head>
  <body>
    <template>
      <style>{FONTS}
      #{ident} {{ position: absolute; inset: 0; overflow: hidden; font-family: "Montserrat", sans-serif; }}
      #{ident} *, #{ident} *::before, #{ident} *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}{SHARED}{css}
      </style>
      <div id="{ident}" data-composition-id="{ident}" data-width="1920" data-height="1080" data-duration="{dur:.2f}">
      {html}
      </div>
      <script>
        const tl = gsap.timeline({{ paused: true }});
        {chr(10).join("        " + line for line in js).lstrip()}
        window.__timelines["{ident}"] = tl;
      </script>
    </template>
  </body>
</html>
"""
    os.makedirs(os.path.join(HERE, "compositions"), exist_ok=True)
    with open(os.path.join(HERE, "compositions", f"{ident}.html"), "w") as f:
        f.write(doc)


def stars():
    rng = random.Random(9)
    out = []
    for _ in range(110):
        x, y = rng.uniform(0, 1920), rng.uniform(0, 1080)
        s = rng.choice([2, 2, 2, 3, 3, 4])
        out.append(f'<div class="star" style="left:{x:.0f}px;top:{y:.0f}px;width:{s}px;height:{s}px"></div>')
    return "\n        ".join(out)


def main():
    builders = {"hook": scene_hook, "dob-grid": scene_dob, "services": scene_services, "promise": scene_promise, "lockup": scene_lockup}
    hosts, sfx_all, music_all, marks = [], [], [], {}
    for k, (ident, (s0, s1)) in enumerate(SCENES.items()):
        res = builders[ident]()
        html, css, js, sfx, music = res[:5]
        if ident == "lockup":
            marks = {"trace": s0 + res[5][0], "word": s0 + res[5][1]}
        write_scene(ident, html, css, js, s1 - s0)
        hosts.append(
            f'<div id="{ident}" data-composition-id="{ident}" data-composition-src="compositions/{ident}.html" data-start="{s0}" '
            f'data-duration="{s1 - s0:.2f}" data-track-index="{2 + k % 2}" data-width="1920" data-height="1080" '
            f'style="position: absolute; inset: 0; z-index: 10"></div>'
        )
        sfx_all += [(n, s0 + t - SFX_LEAD[n], v) for n, t, v in sfx]
        music_all += [{**m, "t": round(s0 + m["t"], 3)} for m in music]
    for ident in ("dob-grid", "services", "promise", "lockup"):
        music_all.append({"type": "bell", "t": SCENES[ident][0] + 0.1, "level": 0.3, "note": 12})
    lanes, tags = [], []
    for i, (n, t, v) in enumerate(sorted(sfx_all, key=lambda x: x[1])):
        dur = min(SFX_DUR[n], TOTAL - t)
        lane = next((k for k, free in enumerate(lanes) if free <= t), None)
        if lane is None:
            lanes.append(0.0)
            lane = len(lanes) - 1
        lanes[lane] = t + dur + 0.01
        tags.append(f'<audio id="sfx-{i:02d}-{n}" src="assets/sfx/{n}.mp3" data-start="{t:.2f}" data-duration="{dur:.2f}" '
                    f'data-track-index="{11 + lane}" data-volume="{v}"></audio>')
    cues = {"seconds": TOTAL, "key": "D", "seed": 5, "drone": {"start": 0.0, "end": TOTAL, "level": 0.5},
            "riser": {"start": marks["word"] - 2.4, "end": marks["word"], "level": 0.3}, "events": music_all, "tail_fade": 0.8}
    with open(os.path.join(HERE, "music-cues.json"), "w") as f:
        json.dump(cues, f, indent=1)
    doc = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>ASTROMITRA RADHAA intro</title>
    <script src="vendor/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #05071a; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #05071a; }}
      #sky {{ position: absolute; inset: 0; background: radial-gradient(circle at 50% 46%, #18205a 0%, #0b1033 48%, #05071a 100%); }}
      #underglow {{ position: absolute; left: 360px; top: 760px; width: 1200px; height: 600px; border-radius: 50%;
        background: radial-gradient(closest-side, rgba(90, 15, 30, 0.45), rgba(90, 15, 30, 0)); }}
      #stars {{ position: absolute; inset: 0; }}
      .star {{ position: absolute; border-radius: 50%; background: #f6ead3; opacity: 0.35; }}
      #fade {{ position: absolute; inset: 0; background: #05071a; z-index: 50; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <!-- generated by build.py -->
      <div id="sky" data-layout-ignore></div>
      <div id="underglow" data-layout-ignore></div>
      <div id="stars" data-layout-ignore>
        {stars()}
      </div>
      {chr(10).join("      " + h for h in hosts).lstrip()}
      <div id="fade" data-layout-ignore></div>
      <audio id="music" src="assets/audio/intro-sting.wav" data-start="0" data-duration="{TOTAL}" data-track-index="10" data-volume="1"></audio>
      {chr(10).join("      " + t for t in tags).lstrip()}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#fade", {{opacity: 1}}, {{opacity: 0, duration: 0.6, ease: "power1.out"}}, 0);
      tl.fromTo(".star", {{opacity: 0.12}}, {{opacity: 0.7, duration: 1.1, stagger: {{each: 0.05, from: "random", yoyo: true, repeat: 15}}, ease: "sine.inOut"}}, 0.3);
      tl.fromTo("#stars", {{x: 0}}, {{x: -60, duration: {TOTAL}, ease: "none"}}, 0);
      tl.to("#fade", {{opacity: 1, duration: 0.45, ease: "power2.in"}}, {TOTAL - 0.45:.2f});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    with open(os.path.join(HERE, "index.html"), "w") as f:
        f.write(doc)
    print(f"index.html + {len(SCENES)} scenes, {TOTAL}s, {len(tags)} sfx, {len(music_all)} music events")


if __name__ == "__main__":
    main()
