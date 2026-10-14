"""Generate index.html for the ASTROMITRA RADHAA channel intro (1920x1080, 7 s).

Run: python3 build.py && npx hyperframes check
"""

import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
TOTAL = 6.3
CX, CY, CELL = 960, 450, 150
GRID = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]  # Lo Shu: every row, column and diagonal sums to 15

# Order the numbers light: centre, odd cross (opposite pairs sum to 10), even corners.
ORDER = [(5, 0.95), (9, 1.12), (1, 1.23), (3, 1.34), (7, 1.45), (4, 1.6), (6, 1.7), (2, 1.8), (8, 1.9)]
NOTES = {5: 0, 9: 2, 1: 4, 3: 7, 7: 9, 4: 12, 6: 14, 2: 16, 8: 19}  # pentatonic climb
T_TRACE, T_RING, T_SHRINK, T_WORD = 2.05, 2.75, 3.0, 3.5


def cell_xy(n):
    for r, row in enumerate(GRID):
        if n in row:
            c = row.index(n)
            return CX + (c - 1) * CELL, CY + (r - 1) * CELL
    raise ValueError(n)


def stars():
    rng = random.Random(9)
    out = []
    for i in range(90):
        x, y = rng.uniform(0, 1920), rng.uniform(0, 1080)
        s = rng.choice([2, 2, 2, 3, 3, 4])
        o = rng.uniform(0.18, 0.6)
        out.append(f'<div class="star" id="st-{i}" style="left:{x:.0f}px;top:{y:.0f}px;width:{s}px;height:{s}px;opacity:{o:.2f}"></div>')
    return "\n      ".join(out)


def lines():
    h = CELL * 1.5
    x0, x1, y0, y1 = CX - h, CX + h, CY - h, CY + h
    grid = [f'<rect id="g-frame" x="{x0}" y="{y0}" width="{2 * h}" height="{2 * h}" rx="6" class="gl" pathLength="1" />']
    for k, v in enumerate((CX - CELL / 2, CX + CELL / 2)):
        grid.append(f'<line id="g-v{k}" x1="{v}" y1="{y0}" x2="{v}" y2="{y1}" class="gl" pathLength="1" />')
    for k, v in enumerate((CY - CELL / 2, CY + CELL / 2)):
        grid.append(f'<line id="g-h{k}" x1="{x0}" y1="{v}" x2="{x1}" y2="{v}" class="gl" pathLength="1" />')
    traces, tags = [], []
    ext = 34
    segs = []
    for r in range(3):
        y = CY + (r - 1) * CELL
        segs.append(((x0 - ext, y), (x1 + ext, y), (x1 + 78, y)))
    for c in range(3):
        x = CX + (c - 1) * CELL
        segs.append(((x, y0 - ext), (x, y1 + ext), (x, y1 + 70)))
    segs.append(((x0 - ext, y0 - ext), (x1 + ext, y1 + ext), (x1 + 66, y1 + 62)))
    segs.append(((x1 + ext, y0 - ext), (x0 - ext, y1 + ext), (x0 - 66, y1 + 62)))
    for i, ((ax, ay), (bx, by), (tx, ty)) in enumerate(segs):
        traces.append(f'<line id="tr-{i}" x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" class="trace" pathLength="1" />')
        tags.append(f'<div id="tag-{i}" class="tag" style="left:{tx - 30}px;top:{ty - 20}px">15</div>')
    ring = [f'<circle id="ring" cx="{CX}" cy="{CY}" r="322" class="ring" pathLength="1" />',
            f'<circle id="ring-in" cx="{CX}" cy="{CY}" r="300" class="ring-in" pathLength="1" />']
    for k in range(9):
        a = math.radians(-90 + 40 * k)
        ring.append(f'<circle id="dot-{k}" cx="{CX + 322 * math.cos(a):.1f}" cy="{CY + 322 * math.sin(a):.1f}" r="11" class="dot" />')
    return "\n          ".join(grid + traces + ring), "\n        ".join(tags)


def numbers():
    out = []
    for n in range(1, 10):
        x, y = cell_xy(n)
        cls = "num num-center" if n == 5 else ("num num-odd" if n % 2 else "num num-even")
        out.append(f'<div id="n-{n}" class="{cls}" style="left:{x - 60}px;top:{y - 60}px">{n}</div>')
    return "\n        ".join(out)


def timeline():
    js = []
    a = js.append
    a('tl.fromTo("#sky", {opacity: 0}, {opacity: 1, duration: 0.5, ease: "power1.out"}, 0);')
    a('tl.fromTo(".star", {scale: 0.2}, {scale: 1, duration: 0.8, stagger: {each: 0.006, from: "random"}, ease: "power2.out"}, 0.05);')
    a(f'tl.fromTo(".star", {{opacity: 0.15}}, {{opacity: 0.75, duration: 0.9, stagger: {{each: 0.04, from: "random", yoyo: true, repeat: 7}}, ease: "sine.inOut", immediateRender: false}}, 0.9);')
    a('tl.fromTo("#spark", {scale: 0, opacity: 0}, {scale: 1, opacity: 1, duration: 0.35, ease: "expo.out"}, 0.05);')
    a('tl.to("#spark", {scale: 2.6, opacity: 0, duration: 0.45, ease: "power2.in"}, 0.4);')
    a('tl.fromTo("#g-frame", {strokeDashoffset: 1}, {strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut"}, 0.35);')
    for k, el in enumerate(["#g-v0", "#g-v1", "#g-h0", "#g-h1"]):
        a(f'tl.fromTo("{el}", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 0.42, ease: "power2.out"}}, {0.5 + 0.07 * k:.2f});')
    for n, t in ORDER:
        a(f'tl.fromTo("#n-{n}", {{scale: 1.8, opacity: 0, y: -10}}, {{scale: 1, opacity: 1, y: 0, duration: 0.42, ease: "back.out(2.2)"}}, {t});')
    a('tl.fromTo("#halo", {scale: 0.3, opacity: 0}, {scale: 1, opacity: 1, duration: 0.6, ease: "power2.out"}, 0.95);')
    for i in range(8):
        t = T_TRACE + 0.07 * i
        a(f'tl.fromTo("#tr-{i}", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 0.32, ease: "power2.out"}}, {t:.2f});')
        a(f'tl.fromTo("#tag-{i}", {{scale: 0, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.6)"}}, {t + 0.2:.2f});')
    a(f'tl.to(".trace", {{opacity: 0, duration: 0.35}}, {T_RING:.2f});')
    a(f'tl.to(".tag", {{scale: 0.4, opacity: 0, duration: 0.3, ease: "power2.in"}}, {T_RING:.2f});')
    a(f'tl.fromTo("#ring", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 0.6, ease: "power2.inOut"}}, {T_RING:.2f});')
    a(f'tl.fromTo("#ring-in", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 0.6, ease: "power2.inOut"}}, {T_RING + 0.08:.2f});')
    a(f'tl.fromTo(".dot", {{scale: 0, transformOrigin: "50% 50%"}}, {{scale: 1, duration: 0.35, stagger: 0.04, ease: "back.out(3)"}}, {T_RING + 0.1:.2f});')
    a(f'tl.to("#seal", {{scale: 0.52, y: -122, duration: 0.65, ease: "power3.inOut"}}, {T_SHRINK:.2f});')
    a(f'tl.fromTo("#flash", {{opacity: 0, scale: 0.6}}, {{opacity: 1, scale: 1.4, duration: 0.18, ease: "power2.out"}}, {T_WORD - 0.05:.2f});')
    a(f'tl.to("#flash", {{opacity: 0, duration: 0.6, ease: "power2.in"}}, {T_WORD + 0.15:.2f});')
    a(f'tl.fromTo(".ch", {{opacity: 0, y: 46, scale: 1.25}}, {{opacity: 1, y: 0, scale: 1, duration: 0.55, stagger: {{each: 0.035, from: "center"}}, ease: "expo.out"}}, {T_WORD - 0.12:.2f});')
    a(f'tl.fromTo("#rule", {{scaleX: 0}}, {{scaleX: 1, duration: 0.5, ease: "power3.out"}}, {T_WORD + 0.4:.2f});')
    a(f'tl.fromTo("#services", {{opacity: 0, y: 18}}, {{opacity: 1, y: 0, duration: 0.45, ease: "power3.out"}}, {T_WORD + 0.55:.2f});')
    a(f'tl.fromTo("#tagline", {{opacity: 0, y: 18}}, {{opacity: 1, y: 0, duration: 0.45, ease: "power3.out"}}, {T_WORD + 0.8:.2f});')
    a(f'tl.fromTo("#glint", {{scale: 0, rotation: -45, opacity: 0}}, {{scale: 1, rotation: 0, opacity: 1, duration: 0.35, ease: "back.out(2)"}}, {T_WORD + 1.15:.2f});')
    a(f'tl.to("#glint", {{scale: 0.2, rotation: 45, opacity: 0, duration: 0.45, ease: "power2.in"}}, {T_WORD + 1.52:.2f});')
    a(f'tl.to("#all", {{opacity: 0, duration: 0.45, ease: "power2.in"}}, {TOTAL - 0.45:.2f});')
    return "\n      ".join(x for x in js if x)


def word_chars():
    return "".join('<span class="sp"></span>' if c == " " else f'<span class="ch">{c}</span>' for c in "ASTROMITRA RADHAA")


def sfx_tags():
    events = [("whoosh-short", 0.35 - 0.16, 0.35, 0.57), ("ping", T_TRACE - 0.32, 0.25, 1.32),
              ("whoosh-cinematic", T_SHRINK - 0.25, 0.4, 5.54), ("sparkle", T_WORD + 1.15, 0.3, 1.8)]
    out = []
    for i, (name, t, vol, dur) in enumerate(events):
        dur = min(dur, TOTAL - t)
        out.append(f'<audio id="sfx-{i}-{name}" src="assets/sfx/{name}.mp3" data-start="{t:.2f}" data-duration="{dur:.2f}" data-track-index="{11 + i % 2}" data-volume="{vol}"></audio>')
    return "\n      ".join(out)


def music_cues():
    events = [{"type": "pluck", "t": t + 0.02, "level": 0.42, "note": NOTES[n]} for n, t in ORDER]
    events += [{"type": "impact", "t": T_WORD, "level": 0.95}, {"type": "bell", "t": T_WORD, "level": 0.85, "note": 0},
               {"type": "bell", "t": T_WORD + 1.15, "level": 0.35, "note": 7}, {"type": "shimmer", "t": T_TRACE, "level": 0.35},
               {"type": "shimmer", "t": T_WORD + 1.1, "level": 0.4}]
    return {"seconds": TOTAL, "key": "D", "seed": 5, "drone": {"start": 0.0, "end": TOTAL, "level": 0.5},
            "riser": {"start": T_TRACE - 0.4, "end": T_WORD, "level": 0.3}, "events": events, "tail_fade": 0.6}


CSS = """
      @font-face { font-family: "Cinzel"; src: url("assets/fonts/cinzel-latin-600-normal.woff2") format("woff2"); font-weight: 600; }
      @font-face { font-family: "Cinzel"; src: url("assets/fonts/cinzel-latin-700-normal.woff2") format("woff2"); font-weight: 700; }
      @font-face { font-family: "Montserrat"; src: url("assets/fonts/montserrat-latin-wght.woff2") format("woff2"); font-weight: 100 900; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #05071a; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #05071a; font-family: "Montserrat", sans-serif; }
      #all, #sky, #seal, #seal-rot { position: absolute; inset: 0; }
      #sky { background: radial-gradient(circle at 50% 46%, #18205a 0%, #0b1033 48%, #05071a 100%); }
      #underglow { position: absolute; left: 360px; top: 760px; width: 1200px; height: 600px; border-radius: 50%;
        background: radial-gradient(closest-side, rgba(90, 15, 30, 0.45), rgba(90, 15, 30, 0)); }
      .star { position: absolute; border-radius: 50%; background: #f6ead3; }
      #seal { transform-origin: 960px 450px; }
      #seal-rot { transform-origin: 960px 450px; }
      svg { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: visible; }
      .gl { fill: none; stroke: #d4a84b; stroke-width: 3; stroke-dasharray: 1; stroke-dashoffset: 1; stroke-linecap: round; }
      .trace { fill: none; stroke: #f3d98b; stroke-width: 4; stroke-dasharray: 1; stroke-dashoffset: 1; stroke-linecap: round; opacity: 0.85; }
      .ring { fill: none; stroke: #d4a84b; stroke-width: 3; stroke-dasharray: 1; stroke-dashoffset: 1; }
      .ring-in { fill: none; stroke: #d4a84b; stroke-width: 1.5; stroke-dasharray: 1; stroke-dashoffset: 1; opacity: 0.45; }
      .dot { fill: #e07a1f; stroke: #f3d98b; stroke-width: 2; }
      #spark { position: absolute; left: 900px; top: 390px; width: 120px; height: 120px; border-radius: 50%;
        background: radial-gradient(closest-side, #fff6dc, rgba(243, 217, 139, 0.7) 30%, rgba(224, 122, 31, 0) 100%); }
      #halo { position: absolute; left: 860px; top: 350px; width: 200px; height: 200px; border-radius: 50%;
        background: radial-gradient(closest-side, rgba(243, 217, 139, 0.42), rgba(243, 217, 139, 0)); }
      .num { position: absolute; width: 120px; height: 120px; display: flex; align-items: center; justify-content: center;
        font: 700 86px/1 "Cinzel"; color: #f6ead3; text-shadow: 0 0 18px rgba(212, 168, 75, 0.45); }
      .num-center { color: #f3d98b; }
      .num-odd { color: #f6ead3; }
      .num-even { color: #d4a84b; }
      .tag { position: absolute; width: 60px; height: 40px; border-radius: 20px; display: flex; align-items: center; justify-content: center;
        background: #5a0f1e; border: 2px solid #e07a1f; color: #f6ead3; font: 800 22px/1 "Montserrat"; }
      #flash { position: absolute; left: 560px; top: 420px; width: 800px; height: 420px; border-radius: 50%;
        background: radial-gradient(closest-side, rgba(255, 240, 200, 0.28), rgba(243, 217, 139, 0)); }
      #lockup { position: absolute; left: 0; right: 0; top: 570px; display: flex; flex-direction: column; align-items: center; }
      #word-wrap { position: relative; padding: 6px 30px; }
      #word { display: flex; gap: 8px; font: 700 112px/1.05 "Cinzel"; white-space: nowrap;
        filter: drop-shadow(0 4px 18px rgba(212, 168, 75, 0.35)); }
      .ch { display: inline-block; color: #f3d98b;
        background: linear-gradient(180deg, #fbe7a8 0%, #f3d98b 35%, #d4a84b 70%, #a87b2e 100%);
        -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
      .sp { display: inline-block; width: 38px; }
      #glint { position: absolute; right: 10px; top: -14px; width: 70px; height: 70px;
        background: radial-gradient(closest-side, #fffaf0, rgba(243, 217, 139, 0.6) 25%, rgba(243, 217, 139, 0) 70%),
          linear-gradient(0deg, rgba(0,0,0,0) 46%, #fff6dc 50%, rgba(0,0,0,0) 54%),
          linear-gradient(90deg, rgba(0,0,0,0) 46%, #fff6dc 50%, rgba(0,0,0,0) 54%); }
      #rule { width: 760px; height: 3px; margin-top: 18px; background: linear-gradient(90deg, rgba(224, 122, 31, 0), #e07a1f 20%, #f3d98b 50%, #e07a1f 80%, rgba(224, 122, 31, 0)); }
      #services { margin-top: 26px; font: 600 26px/1 "Montserrat"; letter-spacing: 0.2em; color: #f6ead3; text-transform: uppercase; }
      #tagline { margin-top: 22px; font: 600 36px/1 "Cinzel"; letter-spacing: 0.08em; color: #d4a84b; }
"""


def main():
    svg_lines, tags = lines()
    doc = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>ASTROMITRA RADHAA intro</title>
    <script src="vendor/gsap.min.js"></script>
    <style>{CSS}    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <!-- generated by build.py -->
      <div id="all">
      <div id="sky" data-layout-ignore></div>
      <div id="underglow" data-layout-ignore></div>
      {stars()}
      <div id="spark" data-layout-ignore></div>
      <div id="seal" data-layout-allow-overflow>
        <div id="halo" data-layout-ignore></div>
        <div id="seal-rot" data-layout-allow-overflow>
        <svg viewBox="0 0 1920 1080" aria-hidden="true">
          {svg_lines}
        </svg>
        </div>
        {numbers()}
        {tags}
      </div>
      <div id="flash" data-layout-ignore></div>
      <div id="lockup">
        <div id="word-wrap"><div id="word" aria-label="ASTROMITRA RADHAA">{word_chars()}</div><div id="glint" data-layout-ignore></div></div>
        <div id="rule"></div>
        <div id="services">Astro Numerology &#183; Lo Shu Grid &#183; Future Forecasting &#183; Life Management</div>
        <div id="tagline">Know your numbers. Manage your life.</div>
      </div>
      </div>
      <audio id="music" src="assets/audio/intro-sting.wav" data-start="0" data-duration="{TOTAL}" data-track-index="10" data-volume="1"></audio>
      {sfx_tags()}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {timeline()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    with open(os.path.join(HERE, "index.html"), "w") as f:
        f.write(doc)
    with open(os.path.join(HERE, "music-cues.json"), "w") as f:
        json.dump(music_cues(), f, indent=1)
    print("index.html + music-cues.json written")


if __name__ == "__main__":
    main()
