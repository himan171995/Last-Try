"""Generate the YouTube cover images as two one-frame HyperFrames projects.

  cover/short/  1080x1920 cover for the Short
  cover/wide/   1280x720 custom thumbnail

Inputs in each cover/<name>/assets/: doc_cutout.png (doctor cut out from the 1:53.5 source frame,
EDSR x4 upscaled, background removed), bg_plate.jpg (the same frame, blurred), fonts and icons.
Run: python3 build/cover.py && npx hyperframes snapshot cover/short --at 0.5 --no-end (same for wide)
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

FONTS = """
@font-face { font-family: "Fraunces"; src: url("assets/fraunces-latin-full.woff2") format("woff2"); font-weight: 100 900; }
@font-face { font-family: "Montserrat"; src: url("assets/montserrat-latin-wght.woff2") format("woff2"); font-weight: 100 900; }
@font-face { font-family: "Noto Serif Devanagari"; src: url("assets/noto-serif-devanagari-devanagari-700-normal.woff2") format("woff2"); font-weight: 700; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:"Montserrat", sans-serif; color:#fff; }
#root { position:relative; width:100%; height:100%; overflow:hidden; background:#06111d; }
.layer { position:absolute; inset:0; }
.plate { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:brightness(0.42) saturate(0.9); }
.ico { display:block; object-fit:contain; filter:drop-shadow(0 10px 18px rgba(0,0,0,0.45)); }
.doc { position:absolute; display:block;
  filter: drop-shadow(0 0 2px rgba(255,236,200,0.55)) drop-shadow(0 40px 60px rgba(0,0,0,0.6));
  -webkit-mask-image: linear-gradient(180deg, #000 0%, #000 70%, transparent 96%), linear-gradient(90deg, transparent 0%, #000 16%);
  -webkit-mask-composite: source-in; mask-image: linear-gradient(180deg, #000 0%, #000 70%, transparent 96%), linear-gradient(90deg, transparent 0%, #000 16%);
  mask-composite: intersect; }
.kicker { font-weight:800; letter-spacing:0.24em; color:#ffc845; }
.big { font-weight:900; line-height:0.92; letter-spacing:-0.01em;
  background:linear-gradient(180deg, #ffffff 0%, #ffd9d4 55%, #ff7a6e 100%); -webkit-background-clip:text; background-clip:text; color:transparent;
  filter: drop-shadow(0 8px 0 rgba(120,20,20,0.55)) drop-shadow(0 18px 30px rgba(0,0,0,0.55)); }
.sub { font-family:"Fraunces", serif; font-style:italic; font-weight:800; color:#ffc845; line-height:1.0; text-shadow:0 8px 26px rgba(0,0,0,0.6); }
.chip { display:flex; align-items:center; gap:16px; border-radius:24px; background:rgba(7,19,31,0.82); border:2px solid rgba(255,200,69,0.35); font-weight:800; }
.name { font-family:"Fraunces", serif; font-weight:800; line-height:1; }
.hosp { font-weight:800; color:#7ff0e0; }
"""

CAUSES = [("anxious", "Stress"), ("milk", "Zyada doodh, dahi, ghee"), ("rice", "Naya chaawal, anaaj"), ("candy", "Baar-baar meetha")]


def page(w, h, css, body):
    return f"""<!doctype html>
<html lang="hi-Latn">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <title>Cover</title>
    <script src="assets/gsap.min.js"></script>
    <style>html, body {{ width:{w}px; height:{h}px; overflow:hidden; background:#06111d; }}{FONTS}{css}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="1" data-width="{w}" data-height="{h}">
{body}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def icon(name, size):
    return f'<img class="ico" src="assets/{name}.webp" alt="" style="width:{size}px;height:{size}px" />'


# ------------------------------------------------------------------ 1080x1920 Short cover
short_css = """
.glow { position:absolute; left:60px; top:520px; width:960px; height:960px; border-radius:50%;
  background:radial-gradient(circle, rgba(43,212,196,0.38) 0%, rgba(43,212,196,0.10) 45%, rgba(43,212,196,0) 70%); }
.shade { position:absolute; inset:0; background:
  linear-gradient(180deg, rgba(5,13,23,0.92) 0%, rgba(5,13,23,0.55) 30%, rgba(5,13,23,0.10) 50%, rgba(5,13,23,0.55) 72%, rgba(5,13,23,0.96) 100%); }
.top { position:absolute; left:0; right:0; top:150px; text-align:center; }
.top .kicker { font-size:34px; }
.top .big { font-size:196px; margin-top:24px; }
.top .sub { font-size:104px; margin-top:12px; }
.causes { position:absolute; left:56px; right:56px; top:1372px; display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.causes .chip { padding:14px 20px; font-size:38px; line-height:1.1; }
.causes-h { position:absolute; left:0; right:0; top:1300px; text-align:center; font-weight:900; font-size:40px; letter-spacing:0.18em; color:#7ff0e0; }
.brand { position:absolute; left:0; right:0; top:1640px; display:flex; flex-direction:column; align-items:center; }
.brand .name { font-size:84px; }
.brand .rule { width:360px; height:5px; border-radius:3px; margin:16px 0 14px; background:linear-gradient(90deg, transparent, #ffc845, transparent); }
.brand .hosp { font-size:38px; }
"""
chips = "".join(f'<div class="chip">{icon(i, 76)}<span>{t}</span></div>' for i, t in CAUSES)
short_body = f"""
      <img class="plate" src="assets/bg_plate.jpg" alt="" />
      <div class="glow"></div>
      <img class="doc" src="assets/doc_cutout.png" alt="" style="left:60px; top:590px; width:900px; height:auto;" />
      <div class="shade"></div>
      <div class="top">
        <div class="kicker">AYURVED &middot; CHARAKA SAMHITA</div>
        <div class="big">DIABETES</div>
        <div class="sub">kyun badh raha hai?</div>
      </div>
      <div class="causes-h">4 KAARAN</div>
      <div class="causes">{chips}</div>
      <div class="brand">
        <div class="name">Dr. Mohan Padole</div>
        <div class="rule"></div>
        <div class="hosp">Saikrupa Ayurvedic Hospital, Nagpur</div>
      </div>"""

# ------------------------------------------------------------------ 1280x720 thumbnail
wide_css = """
.glow { position:absolute; left:640px; top:-60px; width:760px; height:760px; border-radius:50%;
  background:radial-gradient(circle, rgba(43,212,196,0.40) 0%, rgba(43,212,196,0.10) 45%, rgba(43,212,196,0) 70%); }
.shade { position:absolute; inset:0; background:linear-gradient(90deg, rgba(5,13,23,0.97) 0%, rgba(5,13,23,0.88) 42%, rgba(5,13,23,0.25) 70%, rgba(5,13,23,0.35) 100%); }
.shade2 { position:absolute; inset:0; background:linear-gradient(0deg, rgba(5,13,23,0.85) 0%, rgba(5,13,23,0) 30%); }
.left { position:absolute; left:56px; top:46px; width:700px; }
.left .kicker { font-size:22px; }
.left .big { font-size:122px; margin-top:14px; }
.left .sub { font-size:68px; margin-top:8px; }
.icons { display:flex; gap:12px; margin-top:28px; }
.icons .chip { flex-direction:column; gap:6px; padding:12px 10px 10px; width:160px; font-size:19px; text-align:center; line-height:1.1; }
.brand { position:absolute; left:56px; bottom:34px; display:flex; align-items:baseline; gap:18px; }
.brand .name { font-size:46px; }
.brand .hosp { font-size:22px; }
"""
wide_icons = "".join(f'<div class="chip">{icon(i, 60)}<span>{t}</span></div>' for i, t in CAUSES)
wide_body = f"""
      <img class="plate" src="assets/bg_plate.jpg" alt="" style="object-position:50% 35%;" />
      <div class="glow"></div>
      <img class="doc" src="assets/doc_cutout.png" alt="" style="left:600px; top:36px; height:790px; width:auto;" />
      <div class="shade"></div>
      <div class="shade2"></div>
      <div class="left">
        <div class="kicker">AYURVED &middot; CHARAKA SAMHITA</div>
        <div class="big">DIABETES</div>
        <div class="sub">kyun badh raha hai?</div>
        <div class="icons">{wide_icons}</div>
      </div>
      <div class="brand"><div class="name">Dr. Mohan Padole</div><div class="hosp">Saikrupa Ayurvedic Hospital, Nagpur</div></div>"""

for name, (w, h, css, body) in {"short": (1080, 1920, short_css, short_body), "wide": (1280, 720, wide_css, wide_body)}.items():
    d = os.path.join(ROOT, "cover", name)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w").write(page(w, h, css, body))
    open(os.path.join(d, "hyperframes.json"), "w").write('{\n  "paths": { "assets": "assets" }\n}\n')
print("wrote cover/short and cover/wide")
