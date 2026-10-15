"""Generate index.html for the piles Q&A edit (1920x1080, 30 fps, exactly 60.00 s).

Run: python3 build/edl.py && python3 -I build/aroll.py GRADED SOURCE && python3 build/compose.py

The graded, cut A-roll plays full frame inside #cam; framing (punch-ins 100/120/140/160 %, slow
push-ins, reaction cutaways on the young doctor) is GSAP transforms on #cam, switched on the cut
points. Graphics are white-and-gold cards anchored to spoken words via at(). Captions are
word-highlighted, 2-4 words per line. SFX cues are written to build/sfx.json for build/mix.py.
"""

from kit import *  # noqa: F401,F403  (helpers: at, sec, clip, full, icon, tw, sfx, pop_in, ...)
from kit import BODY, FULL, JS, SFX, WORDS, SPEECH_END, TOTAL, W, H, rnd

GOLD = "#E8B44A"
TAKE_END = 57.0            # takeaway card holds until here, end card to 60.00
SEGS = EDIT["segments"]

# ================================================================== CAMERA
# preset -> (scale, origin x %, origin y %); origins sit on the subject's face so it stays put.
PRESET = {
    "WIDE": (1.0, 50, 50), "DOC_120": (1.2, 34, 39), "DOC_140": (1.4, 34, 39), "DOC_160": (1.6, 34, 38),
    "A_130": (1.3, 53, 18), "YOUNG": (1.9, 100, 37),
}
CAM = [  # (start, preset, push-to scale or None)
    (0.0, "DOC_140", 1.5),
    (sec("question"), "A_130", 1.38),
    (sec("answer"), "WIDE", 1.05),
    (at("ki", sec("answer")) - 0.12, "DOC_120", 1.27),
    (at("iska") - 0.1, "DOC_140", 1.5),
    (sec("routine"), "DOC_120", 1.25),
    (sec("clean"), "DOC_140", 1.48),
    (at("woh", sec("clean")) - 0.12, "DOC_160", 1.7),
    (sec("advice"), "WIDE", 1.04),
    (at("ki", sec("advice")) - 0.12, "DOC_120", 1.26),
    (at("anus", sec("advice")) - 0.15, "YOUNG", 1.95),
    (at("thoda") - 0.15, "DOC_140", 1.5),
    (sec("takeaway"), "DOC_160", 1.75),
]
for i, (t0, name, push) in enumerate(CAM):
    t1 = CAM[i + 1][0] if i + 1 < len(CAM) else SPEECH_END
    s, ox, oy = PRESET[name]
    tw(f'tl.set("#cam", {{scale:{s}, x:0, transformOrigin:"{ox}% {oy}%"}}, {f(t0)});')
    if push:
        tw(f'tl.to("#cam", {{scale:{push}, duration:{f(t1 - t0)}, ease:"sine.inOut"}}, {f(t0 + 0.001)});')

# zoom-snap on the hook's key word, whip-pan from hook to question
tw(f'tl.fromTo("#camfx", {{scale:1}}, {{scale:1.06, duration:0.12, yoyo:true, repeat:1, ease:"power2.out"}}, {f(at("baar-baar") - 0.05)});')
q0 = sec("question")
tw(f'tl.fromTo("#camfx", {{x:0, filter:"blur(0px)"}}, {{x:-260, filter:"blur(14px)", duration:0.13, ease:"power2.in"}}, {f(q0 - 0.13)});')
tw(f'tl.fromTo("#camfx", {{x:260, filter:"blur(14px)"}}, {{x:0, filter:"blur(0px)", duration:0.14, ease:"power2.out", immediateRender:false}}, {f(q0)});')
sfx("whoosh-short", q0 - 0.18, 0.4)


def card(ident, start, end, inner, pos="right", z=20):
    clip(ident, start, end, f'<div id="{ident}-in" class="card {pos}">{inner}</div>', "", z, 2)
    tw(f'tl.fromTo("#{ident}-in", {{opacity:0, x:{60 if pos == "right" else -60}}}, {{opacity:1, x:0, duration:0.45, ease:"power3.out"}}, {f(start)});')
    tw(f'tl.to("#{ident}-in", {{opacity:0, x:{40 if pos == "right" else -40}, duration:0.3, ease:"power2.in"}}, {f(end - 0.3)});')


# ================================================================== HOOK (0 - 3.9)
h1 = sec("question")
clip("hook-title", 0.05, h1 - 0.05, """
<div class="hook" id="hk"><div class="hook-k" id="hk-k">PILES &middot; FISSURE</div>
<div class="hook-t"><span class="hm"><span class="hw" id="hw0">Baar-baar</span></span> <span class="hm"><span class="hw gold" id="hw1">kyun</span></span> <span class="hm"><span class="hw" id="hw2">hota hai?</span></span></div></div>""", "", 25, 2)
rise_in("#hk-k", 0.12, 0.35, 16)
tw('tl.fromTo(".hw", {yPercent:110}, {yPercent:0, duration:0.4, stagger:0.09, ease:"power4.out"}, 0.2);')
tw(f'tl.to("#hk", {{opacity:0, y:-30, duration:0.25, ease:"power2.in"}}, {f(h1 - 0.35)});')
sfx("riser", 0.0, 0.3)
sfx("impact-bass-1", 0.22, 0.4)

# ================================================================== QUESTION (Shot A)
t_piles = at("piles", q0)
t_rec = at("recurrent")
anat_small = """<svg class="anat-mini" viewBox="0 0 300 340" width="300" height="340">
  <path d="M95 10 C95 90 110 160 128 220 L136 300 M205 10 C205 90 190 160 172 220 L164 300" fill="none" stroke="#e7a3a3" stroke-width="22" stroke-linecap="round"/>
  <path d="M95 10 C95 90 110 160 128 220 L136 300 M205 10 C205 90 190 160 172 220 L164 300" fill="none" stroke="#f6c9c4" stroke-width="10" stroke-linecap="round"/>
  <circle cx="122" cy="200" r="15" fill="#b4587a"/><circle cx="180" cy="215" r="13" fill="#b4587a"/>
  <circle cx="132" cy="312" r="13" fill="#9c4a6c"/>
  <path d="M168 262 l10 12" stroke="#7a2b2b" stroke-width="5" stroke-linecap="round"/>
</svg>"""
card("q-terms", t_piles - 0.15, at("lekin") - 0.05, f"""
  <div class="c-k">SAWAAL</div>
  <div class="row">{anat_small}<div class="terms">
    <div class="term" id="qt0"><span class="dot pile"></span>Piles</div>
    <div class="term" id="qt1"><span class="dot fis"></span>Fissure</div>
    <div class="term ok" id="qt2">{icon("check", 54)}Theek bhi ho jaata hai</div></div></div>""", "left")
pop_in("#qt0", t_piles, 0.4, 0.6)
pop_in("#qt1", at("fissure") - 0.05, 0.4, 0.6)
pop_in("#qt2", at("theek", q0) - 0.05, 0.4, 0.6)
sfx("pop", t_piles, 0.3)
sfx("pop", at("fissure"), 0.3)
card("q-loop", at("lekin") - 0.05, sec_end("question") + 0.05, f"""
  <div class="loop">
    <svg class="loop-ring" viewBox="0 0 320 320" width="320" height="320"><circle id="lr" cx="160" cy="160" r="128" fill="none" stroke="{GOLD}" stroke-width="12" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" transform="rotate(-90 160 160)"/></svg>
    <div class="loop-c">{icon("repeat", 120, "lr-ic")}</div>
  </div>
  <div class="loop-l"><div class="big" id="ql1">4&ndash;6 mahine baad</div><div class="big gold-t" id="ql2">Recurrent</div><div class="small" id="ql3">Aisa kyun?</div></div>""", "left")
tw(f'tl.fromTo("#lr", {{strokeDashoffset:1}}, {{strokeDashoffset:0, duration:1.6, ease:"power2.inOut"}}, {f(at("chaar-chhe") - 0.1)});')
tw(f'tl.fromTo("#lr-ic", {{rotation:0}}, {{rotation:360, duration:1.6, ease:"power2.inOut"}}, {f(at("chaar-chhe") - 0.1)});')
pop_in("#ql1", at("chaar-chhe") - 0.05, 0.4, 0.7)
pop_in("#ql2", t_rec - 0.05, 0.4, 0.7)
pop_in("#ql3", at("aisa") - 0.05, 0.4, 0.7)
sfx("whoosh-short", at("lekin") - 0.1, 0.3)
sfx("ping", t_rec, 0.3)

# ================================================================== ANATOMY B-ROLL (gap + answer start)
g = EDIT["gaps"][0]
an0, an1 = g["start"] - 0.05, at("ki", sec("answer")) - 0.12
anat = """<svg class="anat" viewBox="0 0 700 760" width="700" height="760">
  <defs>
    <linearGradient id="wall" x1="0" x2="1"><stop offset="0" stop-color="#d98a8a"/><stop offset="0.5" stop-color="#f1b3ad"/><stop offset="1" stop-color="#d98a8a"/></linearGradient>
    <radialGradient id="pile" cx="0.4" cy="0.35" r="0.7"><stop offset="0" stop-color="#d27aa0"/><stop offset="1" stop-color="#8e3f63"/></radialGradient>
  </defs>
  <path id="an-lumen" d="M250 40 C250 200 270 330 305 470 L320 650 L380 650 L395 470 C430 330 450 200 450 40 Z" fill="#fff4ef"/>
  <path id="an-wl" d="M250 40 C250 200 270 330 305 470 L320 650" fill="none" stroke="url(#wall)" stroke-width="46" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>
  <path id="an-wr" d="M450 40 C450 200 430 330 395 470 L380 650" fill="none" stroke="url(#wall)" stroke-width="46" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>
  <path d="M286 452 L414 452" stroke="#c98b6a" stroke-width="3" stroke-dasharray="8 8" opacity="0.8"/>
  <g id="an-int"><ellipse cx="300" cy="420" rx="26" ry="34" fill="url(#pile)"/><ellipse cx="402" cy="440" rx="24" ry="30" fill="url(#pile)"/></g>
  <g id="an-ext"><ellipse cx="318" cy="668" rx="28" ry="22" fill="url(#pile)"/></g>
  <path id="an-fis" d="M384 560 l18 30" stroke="#7a2b2b" stroke-width="7" stroke-linecap="round"/>
  <circle id="an-ring" cx="350" cy="660" r="62" fill="none" stroke="#E8B44A" stroke-width="8" opacity="0"/>
</svg>"""
full("anatomy", an0, an1, f"""
<div id="an-in" class="scene light">
  <div class="sc-title" id="an-t">Piles aur Fissure</div>
  <div class="an-wrap">{anat}
    <div class="lbl l1" id="al1"><span class="ln"></span>Rectum</div>
    <div class="lbl l2" id="al2"><span class="ln"></span>Internal piles</div>
    <div class="lbl l3" id="al3"><span class="ln"></span>Fissure</div>
    <div class="lbl l4" id="al4"><span class="ln"></span>External piles</div>
    <div class="lbl l5" id="al5"><span class="ln"></span>Anus dwaar</div>
  </div>
</div>""", z=30)
tw(f'tl.fromTo("#an-in", {{opacity:0, scale:1.08, filter:"blur(10px)"}}, {{opacity:1, scale:1, filter:"blur(0px)", duration:0.25, ease:"power2.out"}}, {f(an0)});')
rise_in("#an-t", an0 + 0.1, 0.4, 20)
tw(f'tl.fromTo(["#an-wl","#an-wr"], {{strokeDashoffset:1}}, {{strokeDashoffset:0, duration:0.8, ease:"power2.inOut"}}, {f(an0 + 0.1)});')
tw(f'tl.fromTo("#an-int", {{scale:0, transformOrigin:"50% 50%"}}, {{scale:1, duration:0.4, ease:"back.out(2)"}}, {f(an0 + 0.7)});')
tw(f'tl.fromTo("#an-ext", {{scale:0, transformOrigin:"50% 50%"}}, {{scale:1, duration:0.4, ease:"back.out(2)"}}, {f(an0 + 0.95)});')
tw(f'tl.fromTo("#an-fis", {{opacity:0}}, {{opacity:1, duration:0.3}}, {f(an0 + 1.15)});')
for k, dt in enumerate([0.35, 0.8, 1.2, 1.0, 1.5]):
    pop_in(f"#al{k + 1}", an0 + dt, 0.4, 0.6)
tw(f'tl.fromTo("#an-ring", {{opacity:0, scale:0.6, transformOrigin:"50% 50%"}}, {{opacity:1, scale:1, duration:0.4, ease:"back.out(2)"}}, {f(an0 + 1.6)});')
tw(f'tl.to("#an-in", {{opacity:0, scale:0.96, filter:"blur(8px)", duration:0.22, ease:"power2.in"}}, {f(an1 - 0.22)});')
sfx("whoosh", an0 - 0.1, 0.4)
sfx("click-soft", an0 + 0.8, 0.3)

# ================================================================== ANSWER
a0 = sec("answer")
lt0 = an1 + 0.1
clip("lower-third", lt0, lt0 + 3.4, """
<div class="lt" id="lt"><div class="lt-bar" id="lt-bar"></div><div class="lt-p" id="lt-p">
  <div class="lt-n">Dr. Mohan Padole</div><div class="lt-s">Saikrupa Ayurvedic Hospital, Nagpur</div></div></div>""", "", 24, 4)
tw(f'tl.fromTo("#lt-bar", {{scaleY:0}}, {{scaleY:1, duration:0.3, ease:"power3.out"}}, {f(lt0)});')
tw(f'tl.fromTo("#lt-p", {{clipPath:"inset(0% 100% 0% 0%)", opacity:0}}, {{clipPath:"inset(0% 0% 0% 0%)", opacity:1, duration:0.5, ease:"power3.out"}}, {f(lt0 + 0.1)});')
tw(f'tl.to("#lt", {{opacity:0, x:-40, duration:0.3, ease:"power2.in"}}, {f(lt0 + 3.1)});')
sfx("click-soft", lt0 + 0.1, 0.35)
t_har = at("har", a0)
card("a-cycle", t_har - 0.2, at("iska") - 0.1, f"""
  <div class="c-k">PATIENT</div>
  <div class="steps">
    <div class="st" id="as0">{icon("check", 64)}<span>Ek baar theek</span></div>
    <div class="st-a">&rarr;</div>
    <div class="st" id="as1">{icon("calendar", 64)}<span>Har 4&ndash;6 mahine</span></div>
    <div class="st-a">&rarr;</div>
    <div class="st bad" id="as2">{icon("repeat", 64)}<span>Phir wahi problem</span></div>
  </div>""")
pop_in("#as0", t_har - 0.1, 0.4, 0.6)
pop_in("#as1", at("chaar", t_har) - 0.05, 0.4, 0.6)
pop_in("#as2", at("phir") - 0.05, 0.4, 0.6)
sfx("pop", at("chaar", t_har), 0.3)
sfx("pop", at("phir"), 0.3)
t_dw = at("dwaar", a0)
card("a-dwaar", at("iska") + 0.1, sec_end("answer") + 0.1, f"""
  <div class="c-k">MAIN KAARAN</div>
  <div class="row">{anat_small.replace('class="anat-mini"', 'class="anat-mini" id="ad-svg"')}<div class="terms">
    <div class="term big" id="ad0">Anus dwaar</div>
    <div class="term ok" id="ad1">{icon("sparkles", 54)}Saaf</div></div></div>""")
pop_in("#ad0", t_dw - 0.1, 0.4, 0.6)
pop_in("#ad1", at("saaf", a0) - 0.05, 0.4, 0.6)
sfx("ping", at("saaf", a0), 0.3)

# ================================================================== ROUTINE (full-screen B-roll)
r0 = at("to", sec("routine")) - 0.1
r1 = sec_end("routine") + 0.05
items = [("toothbrush", "Brush", "brush"), ("toothbrush", "Daant", "daaton"), ("eye", "Aankhen", "aankhon"), ("nose", "Naak", "naak"), ("ear", "Kaan", "kaan")]
cards_html = "".join(f'<div class="rt" id="rt{k}">{icon(ic, 150)}<div class="rt-l">{lbl}</div><div class="rt-ok" id="rk{k}">{icon("check", 64)}</div></div>'
                     for k, (ic, lbl, _) in enumerate(items[1:]))
full("routine", r0, r1, f"""
<div id="rt-in" class="scene warm">
  <div class="sc-title" id="rt-t">{icon("sunrise", 96)}<span>Subah uthte hi safai</span></div>
  <div class="rt-row">{cards_html}</div>
</div>""", z=30)
tw(f'tl.fromTo("#rt-in", {{clipPath:"inset(0% 0% 0% 100%)"}}, {{clipPath:"inset(0% 0% 0% 0%)", duration:0.24, ease:"power3.out"}}, {f(r0)});')
rise_in("#rt-t", r0 + 0.1, 0.4, 20)
for k, (_, _, wd) in enumerate(items[1:]):
    tt = at(wd, sec("routine"))
    pop_in(f"#rt{k}", tt - 0.15 if k else r0 + 0.25, 0.45, 0.4)
    pop_in(f"#rk{k}", tt + 0.25, 0.35, 0.2)
    sfx("click-soft", tt + 0.25, 0.35)
tw(f'tl.to("#rt-in", {{clipPath:"inset(0% 100% 0% 0%)", duration:0.22, ease:"power3.in"}}, {f(r1 - 0.22)});')
sfx("whoosh", r0 - 0.12, 0.35)
sfx("whoosh-short", r1 - 0.2, 0.3)

# ================================================================== CLEAN
c0 = sec("clean")
t_woh = at("woh", c0)
card("c-dwaar", c0 + 0.1, t_woh - 0.15, f"""
  <div class="c-k">WAISE HI</div>
  <div class="row c">{icon("droplet", 110)}{icon("soap", 110)}</div>
  <div class="big c" id="cd0">Jo dwaar hain</div>
  <div class="small c" id="cd1">woh acche se saaf karein</div>""")
pop_in("#cd0", at("dwaar", c0) - 0.25, 0.45, 0.7)
pop_in("#cd1", at("dwaar", c0) + 0.25, 0.4, 0.7)
sfx("pop", at("dwaar", c0), 0.3)
clip("c-pop", t_woh - 0.05, sec_end("clean") + 0.05, """
<div class="pop" id="cp"><div class="pop-l" id="cp0">Acche se saaf karein</div><div class="pop-l gold-t" id="cp1">= baar-baar problem nahi</div></div>""", "", 22, 2)
pop_in("#cp0", at("saaf", t_woh) - 0.1, 0.45, 0.7)
pop_in("#cp1", at("baar-baar", t_woh) - 0.05, 0.45, 0.7)
tw(f'tl.to("#cp", {{opacity:0, y:-20, duration:0.3}}, {f(sec_end("clean") - 0.25)});')
sfx("pop", at("saaf", t_woh), 0.3)
sfx("ping", at("baar-baar", t_woh), 0.3)
leak(c0, 0.45)

# ================================================================== ADVICE
d0 = sec("advice")
t_thoda = at("thoda")
card("d-advice", d0 + 0.1, at("anus", d0) - 0.2, f"""
  <div class="c-k">DOCTOR KI SALAH</div>
  <div class="row c">{icon("stethoscope", 120)}</div>
  <div class="big c" id="dv0">Patient ko yahi kehna hai</div>""", "right")
card("d-daily", t_thoda - 0.15, sec_end("advice") + 0.05, f"""
  <div class="c-k">SALAH</div>
  <div class="row c">{icon("droplet", 100)}{icon("sparkles", 100)}</div>
  <div class="big c" id="dd0">Thoda clean karna</div>
  <div class="big c gold-t" id="dd1">Hamesha</div>""", "right")
pop_in("#dd0", at("clean") - 0.1, 0.4, 0.7)
pop_in("#dd1", at("hamesha") - 0.05, 0.45, 0.6)
sfx("pop", at("clean"), 0.3)
sfx("ping", at("hamesha"), 0.3)
sfx("whoosh-short", at("anus", d0) - 0.2, 0.25)

# ================================================================== TAKEAWAY
k0 = sec("takeaway")
clip("k-pop", k0 + 0.05, SPEECH_END - 0.55, """
<div class="take" id="tk"><div class="take-l" id="tk0">Baar-baar yeh problem</div><div class="take-l gold-t" id="tk1">nahi aayegi</div></div>""", "", 22, 2)
pop_in("#tk0", at("baar-baar", k0) - 0.1, 0.5, 0.6)
pop_in("#tk1", at("nahi", k0) - 0.05, 0.5, 0.5)
sfx("impact-bass-2", at("nahi", k0) - 0.35, 0.3)
full("takecard", SPEECH_END - 0.6, TAKE_END + 0.25, f"""
<div id="tc-in" class="scene light">
  <div class="tc-q">&ldquo;</div>
  <div class="tc-l" id="tc0">Hamesha clean karna</div>
  <div class="tc-l gold-t" id="tc1">= baar-baar problem nahi aayegi</div>
  <div class="tc-by" id="tc2">&mdash; Dr. Mohan Padole</div>
</div>""", z=35)
tw(f'tl.fromTo("#tc-in", {{opacity:0, scale:1.06, filter:"blur(10px)"}}, {{opacity:1, scale:1, filter:"blur(0px)", duration:0.25}}, {f(SPEECH_END - 0.6)});')
rise_in("#tc0", SPEECH_END - 0.45, 0.4, 24)
rise_in("#tc1", SPEECH_END - 0.25, 0.4, 24)
rise_in("#tc2", SPEECH_END + 0.0, 0.4, 16)

# ================================================================== END CARD
e0 = TAKE_END
full("endcard", e0, TOTAL, f"""
<div id="ec-in" class="scene light">
  <div class="ec-logo" id="ec-logo">{icon("herb", 110)}</div>
  <div class="ec-n" id="ec-n">Dr. Mohan Padole</div>
  <div class="ec-rule" id="ec-rule"></div>
  <div class="ec-s" id="ec-s">Saikrupa Ayurvedic Hospital, Nagpur</div>
  <div class="ec-sub" id="ec-sub">{icon("bell", 60)}<span>Subscribe</span></div>
  <div class="ec-dis" id="ec-dis">For educational purposes only. Consult a doctor before starting any treatment.</div>
</div>""", z=40)
tw(f'tl.fromTo("#ec-in", {{clipPath:"circle(0% at 50% 50%)"}}, {{clipPath:"circle(130% at 50% 50%)", duration:0.25, ease:"power3.out"}}, {f(e0)});')
pop_in("#ec-logo", e0 + 0.15, 0.45, 0.4)
rise_in("#ec-n", e0 + 0.25, 0.45, 26)
tw(f'tl.fromTo("#ec-rule", {{scaleX:0}}, {{scaleX:1, duration:0.45, ease:"power3.out"}}, {f(e0 + 0.4)});')
rise_in("#ec-s", e0 + 0.45, 0.45, 18)
pop_in("#ec-sub", e0 + 0.85, 0.45, 0.6)
tw(f'tl.fromTo("#ec-sub", {{scale:1}}, {{scale:1.06, duration:0.25, yoyo:true, repeat:3, ease:"sine.inOut"}}, {f(e0 + 1.5)});')
rise_in("#ec-dis", e0 + 0.7, 0.4, 10)
sfx("whoosh-cinematic", e0 - 0.15, 0.35)
sfx("chime", e0 + 0.2, 0.35)

# ================================================================== CAPTIONS (2-4 words per line)
cuts = sorted({round(a, 3) for a, b in FULL} | {round(b, 3) for a, b in FULL})
pages, cur = [], []
for w in WORDS:
    crosses = cur and any(cur[0]["start"] < c <= w["start"] for c in cuts)
    brk = cur and (cur[-1]["text"][-1] in ".?" or w["start"] - cur[-1]["end"] > 0.35)
    txt = " ".join(x["text"] for x in cur + [w])
    if cur and (len(cur) >= 4 or len(txt) > 24 or brk or crosses or (cur[-1]["text"][-1] == "," and len(cur) >= 2)):
        pages.append(cur)
        cur = []
    cur.append(w)
pages.append(cur)
for pi, pg in enumerate(pages):
    start = pg[0]["start"] - 0.05
    nxt = pages[pi + 1][0]["start"] - 0.05 if pi + 1 < len(pages) else SPEECH_END
    end = min(nxt, pg[-1]["end"] + 0.5)
    end = min(end, SPEECH_END - 0.62)
    if end - start < 0.2:
        continue
    spans = "".join(f'<span class="cw{" kw" if w["kw"] else ""}" id="cw{pi}-{wi}">{esc(w["text"])}</span>' for wi, w in enumerate(pg))
    onlight = any(x0 - 0.05 <= pg[0]["start"] < x1 for x0, x1 in FULL)
    clip(f"cap{pi}", start, end, f'<div class="cap{" onlight" if onlight else ""}" id="cap{pi}-in">{spans}</div>', "cap-clip", 60, 5)
    tw(f'tl.fromTo("#cap{pi}-in", {{opacity:0, y:14}}, {{opacity:1, y:0, duration:0.14, ease:"power2.out"}}, {f(start)});')
    for wi, w in enumerate(pg):
        tw(f'tl.fromTo("#cw{pi}-{wi}", {{color:"#ffffff"}}, {{color:"{GOLD}", duration:0.06}}, {f(w["start"])});')
        tw(f'tl.to("#cw{pi}-{wi}", {{color:"#ffffff", duration:0.1}}, {f(max(w["end"], w["start"] + 0.12))});')

# ================================================================== DOCUMENT
CSS = open(os.path.join(HERE, "style.css")).read()
GRAIN = ('<svg class="grain" width="1920" height="1080"><filter id="gn"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7"/>'
         '<feColorMatrix values="0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0.9 0"/></filter><rect width="100%" height="100%" filter="url(#gn)"/></svg>')
doc = f"""<!doctype html>
<html lang="hi-Latn">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>Piles: Dr. Mohan Padole</title>
    <script src="vendor/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
      <!-- generated by build/compose.py: edit the generator, then re-run it -->
      <div id="camfx" data-layout-allow-overflow>
        <div id="cam" data-layout-allow-overflow>
          <video id="aroll" class="clip" src="assets/video/aroll.mp4" muted playsinline data-start="0" data-duration="{f(SPEECH_END)}" data-track-index="0"></video>
        </div>
      </div>
      <div class="vignette"></div>
      {GRAIN}
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
json.dump({"total": TOTAL, "speech_end": SPEECH_END, "take_end": TAKE_END}, open(os.path.join(HERE, "meta.json"), "w"), indent=1)
print(f"wrote index.html: {len(BODY)} clips, {len(JS)} tweens, {len(pages)} caption pages, {len(SFX)} sfx")
