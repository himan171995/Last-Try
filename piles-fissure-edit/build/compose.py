"""Generate index.html (the HyperFrames composition) from build/edit.json.

Run: python3 build/edl.py && python3 build/compose.py
"""

import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = "assets/video/aroll.mp4"

with open(os.path.join(HERE, "edit.json")) as f:
    EDIT = json.load(f)

SEGS = EDIT["segments"]
WORDS = EDIT["words"]
PAGES = EDIT["pages"]
SPEECH_END = EDIT["speech_duration"]
END_CARD_IN = round(SPEECH_END - 0.1, 2)
TOTAL = round(END_CARD_IN + 6.0, 2)


def norm(w):
    return re.sub(r"[^a-z\-]", "", w.lower())


def at(word, after=0.0):
    """Output time of the first spoken `word` starting at or after `after`."""
    for w in WORDS:
        if norm(w["text"]) == word and w["start"] >= after - 1e-6:
            return round(w["start"], 2)
    raise KeyError(f"{word} after {after}")


def end_of(word, after=0.0):
    for w in WORDS:
        if norm(w["text"]) == word and w["start"] >= after - 1e-6:
            return round(w["end"], 2)
    raise KeyError(word)


# ---------------------------------------------------------------- timings
T = {}
T["cut_to_doctor"] = SEGS[1]["out_start"]
T["hook_in"], T["hook_out"] = 0.15, round(T["cut_to_doctor"] - 0.1, 2)
T["lt_in"] = round(T["cut_to_doctor"] + 0.45, 2)
T["lt_out"] = round(at("iska") + 0.1, 2)
T["food_in"] = round(at("iska") + 0.05, 2)
T["food_word"] = at("khaan-paan")
T["habits_in"] = round(at("raat") - 0.3, 2)
T["habits_out"] = round(end_of("khaana", at("tala")) + 0.12, 2)
T["chain_in"] = round(at("aur", at("aadat")) - 0.15, 2)
T["chain_steps"] = [at("aur", at("aadat")) + 0.25, at("garam"), at("hard"), at("piles", at("hard"))]
T["chain_out"] = round(end_of("hain", at("tayyar")) + 0.2, 2)
T["morning_in"] = round(at("subah-subah") - 0.25, 2)
T["morning_steps"] = [at("subah-subah") + 0.1, at("stool", at("subah-subah")), at("dard")]
T["morning_pain"] = at("pain", at("dard"))
T["morning_out"] = round(end_of("hai", at("badhta")) + 0.1, 2)
T["sharm_in"] = round(at("sharm") - 0.35, 2)
T["sharm_der"] = at("der")
T["sharm_out"] = round(end_of("hain", at("der")) + 0.05, 2)
T["comp_in"] = round(at("jab", at("der")) - 0.2, 2)
T["comp_steps"] = [at("complication"), at("tabhi")]
T["comp_out"] = round(end_of("hain", at("tabhi")) + 0.15, 2)
T["take_in"] = round(at("khaan-paan", at("samajhna")) - 0.45, 2)
T["take_steps"] = [at("khaan-paan", at("samajhna")), at("aahaar-vihaar"), at("kam"), at("durust")]
T["take_out"] = END_CARD_IN

SPLITS = [(T["chain_in"], T["chain_out"]), (T["take_in"], T["take_out"])]
FULL_BROLL = [(T["habits_in"], T["habits_out"]), (T["morning_in"], T["morning_out"]), (T["comp_in"], T["comp_out"]), (END_CARD_IN, TOTAL)]

# ---------------------------------------------------------------- camera
W, H = 1920, 1080
FRAMES = {
    "W": (1.0, (960, 540), (960, 540)),
    "M": (1.16, (680, 400), (700, 430)),
    "C": (1.30, (680, 380), (760, 420)),
}


def cam_state(name, drift=1.0):
    s, (fx, fy), (tx, ty) = FRAMES[name]
    s *= drift
    x = min(0.0, max(W - W * s, tx - fx * s))
    y = min(0.0, max(H - H * s, ty - fy * s))
    return {"scale": round(s, 4), "x": round(x, 1), "y": round(y, 1)}


def framing_plan():
    plan, cycle, k = [], ["W", "M", "C", "M"], 0
    for i, s in enumerate(SEGS):
        if i == 0:
            plan.append("Q")
            continue
        plan.append(cycle[k % len(cycle)])
        k += 1
    return plan


# ---------------------------------------------------------------- html helpers
def esc(s):
    return html.escape(s, quote=True)


def icon(name, cls="", size=None, ident=None):
    style = f' style="width:{size}px;height:{size}px"' if size else ""
    i = f' id="{ident}"' if ident else ""
    return f'<img{i} class="ico {cls}" src="../assets/icons/{name}.webp" alt=""{style} />'


SCENES = {}
JS = {"main": []}
CUR = ["main"]


def use(scene_id):
    CUR[0] = scene_id
    JS.setdefault(scene_id, [])


def scene(ident, start, end, track, z, inner, css):
    SCENES[ident] = {"start": round(start, 3), "end": round(end, 3), "track": track, "z": z, "html": inner, "css": css}
    return ident


def clip(ident, start, end, track, inner, cls=""):
    dur = round(end - start, 3)
    return (
        f'<div id="{ident}" class="clip {cls}" data-start="{start}" data-duration="{dur}" '
        f'data-track-index="{track}">{inner}</div>'
    )


def broll_inner(ident, scene):
    return f'<div id="{ident}-in" class="broll-in"><div id="{ident}-bar" class="wipe-bar"></div>{scene}</div>'


def decor(prefix, ghost):
    return (
        f'<div class="bg-dots" data-layout-ignore></div>'
        f'<div id="{prefix}-glow-a" class="glow glow-a" data-layout-ignore></div>'
        f'<div id="{prefix}-glow-b" class="glow glow-b" data-layout-ignore></div>'
        f'<div id="{prefix}-ghost" class="ghost" aria-hidden="true" data-layout-ignore>{esc(ghost)}</div>'
    )


# ---------------------------------------------------------------- scenes
def aroll_clips():
    out = []
    for i, s in enumerate(SEGS):
        nxt = SEGS[i + 1]["out_start"] if i + 1 < len(SEGS) else round(s["out_start"] + s["src_out"] - s["src_in"], 3)
        dur = round(nxt - s["out_start"] - 0.001, 3)
        out.append(
            f'<video id="seg-{i:02d}" class="clip aroll" src="{SRC}" playsinline data-has-audio="true" '
            f'data-audio-group="voice" data-start="{s["out_start"]}" data-duration="{dur}" '
            f'data-media-start="{s["src_in"]}" data-track-index="0"></video>'
        )
    return "\n        ".join(out)


def hook():
    inner = (
        '<div id="hook-wrap" class="hook">'
        '<div id="hook-scrim" class="hook-scrim"></div>'
        '<div id="hook-kicker" class="kicker kicker-solid">Doctor se jaaniye</div>'
        '<div id="hook-title" class="hook-title">Piles &amp; Fissure</div>'
        '<div id="hook-rule" class="hook-rule"></div>'
        '<div id="hook-sub" class="hook-sub">aajkal kyun badh rahe hain?</div>'
        "</div>"
    )
    return scene("hook", T["hook_in"], T["hook_out"], 2, 30, inner, ["Hook"])


def lower_third():
    inner = (
        '<div id="lt-wrap" class="lt">'
        '<div id="lt-namebar" class="lt-namebar"><span class="lt-name">Dr. Mohan Padole</span>'
        '<span id="lt-cred" class="lt-cred">BAMS, MD</span></div>'
        f'<div id="lt-rolebar" class="lt-rolebar">{icon("herb", "lt-ico")}'
        "<span>Saikrupa Ayurvedic Clinic, Nagpur</span></div>"
        "</div>"
    )
    return scene("lower-third", T["lt_in"], T["lt_out"] + 0.55, 3, 30, inner, ["Lower third"])


def callout(ident, start, end, ico, label, lines):
    rows = "".join(f'<div id="{ident}-l{i}" class="co-line">{esc(t)}</div>' for i, t in enumerate(lines))
    inner = (
        f'<div id="{ident}-card" class="callout">'
        f'<div class="co-ico-wrap">{icon(ico, "co-ico", ident=f"{ident}-ico")}</div>'
        f'<div class="co-text"><div class="co-label">{esc(label)}</div>{rows}</div>'
        "</div>"
    )
    return scene(ident, start, end, 2, 30, inner, ["Callouts"])


def habits():
    foods = [
        ("curry", "Masaledaar", "masale wala"),
        ("pan", "Tez khaana", "zyada masala"),
        ("chili", "Teekha · Mirchi", "lal mirch"),
        ("fries", "Tala hua", "deep fried"),
    ]
    cards = "".join(
        f'<div id="hab-food-{i}" class="food-card">{icon(ic, "food-ico")}'
        f'<div><div class="food-title">{esc(t)}</div><div class="food-sub">{esc(s)}</div></div></div>'
        for i, (ic, t, s) in enumerate(foods)
    )
    inner = (
        '<div id="hab-wrap" class="scene">'
        + decor("hab", "AADATEIN")
        + '<div class="scene-head"><div id="hab-kicker" class="kicker">Kaaran</div>'
        '<div id="hab-title" class="scene-title">Aajkal ki aadatein</div></div>'
        '<div id="hab-sleep" class="sleep-card">'
        f'<div class="sleep-icons">{icon("moon", "sleep-moon")}{icon("phone", "sleep-phone")}</div>'
        '<div class="sleep-time">12:30 AM</div>'
        '<div class="sleep-title">Raat ko late sona</div>'
        '<div class="sleep-sub">aajkal aam baat</div></div>'
        f'<div class="food-grid">{cards}</div>'
        "</div>"
    )
    return scene("broll-habits", T["habits_in"], T["habits_out"] + 0.45, 4, 20, broll_inner("broll-habits", inner), ["Full-frame scenes", "Habits"])


def chain_panel():
    rows = [
        ("chili", "Masaledaar, teekha, tala", "roz-roz ki aadat"),
        ("fire", "Anna-nalika garam", "pet mein ushnata"),
        ("brick", "Stool hard", "garmi ke kaaran"),
        ("warning", "Piles / Fissure", "tayyar ho jaate hain"),
    ]
    body = "".join(
        f'<div id="ch-row-{i}" class="row"><div class="row-disc">{icon(ic, "row-ico", ident=f"ch-ico-{i}")}</div>'
        f'<div><div class="row-title">{esc(t)}</div><div class="row-sub">{esc(s)}</div></div></div>'
        for i, (ic, t, s) in enumerate(rows)
    )
    inner = (
        '<div id="ch-panel" class="panel">'
        '<div class="panel-head"><div class="kicker">Samjhiye</div>'
        '<div class="panel-title">Kaise banta hai piles?</div></div>'
        '<div class="rows"><div class="rail"><div id="ch-rail-fill" class="rail-fill"></div></div>'
        f"{body}</div></div>"
    )
    return scene("panel-chain", T["chain_in"], T["chain_out"] + 0.5, 5, 20, inner, ["Split-screen panels"])


def morning():
    steps = [("sunrise", "Subah uthte hi", "pehla kaam"), ("toilet", "Stool pass karte waqt", "hard stool"), ("pain", "Dard badhta hai", "anus ke dwaar par")]
    body = ""
    for i, (ic, t, s) in enumerate(steps):
        body += (
            f'<div id="mo-step-{i}" class="step">{icon(ic, "step-ico", ident=f"mo-ico-{i}")}'
            f'<div class="step-num">0{i + 1}</div><div class="step-title">{esc(t)}</div>'
            f'<div class="step-sub">{esc(s)}</div></div>'
        )
        if i < 2:
            body += f'<div class="arrow"><div id="mo-arrow-{i}" class="arrow-line"></div></div>'
    inner = (
        '<div id="mo-wrap" class="scene">'
        + decor("mo", "LAKSHAN")
        + '<div class="scene-head"><div id="mo-kicker" class="kicker">Lakshan</div>'
        '<div id="mo-title" class="scene-title">Subah ka dard</div></div>'
        f'<div class="steps">{body}</div>'
        "</div>"
    )
    return scene("broll-morning", T["morning_in"], T["morning_out"] + 0.45, 4, 20, broll_inner("broll-morning", inner), ["Full-frame scenes", "Morning"])


def complication():
    inner = (
        '<div id="cp-wrap" class="scene">'
        + decor("cp", "DER")
        + '<div class="scene-head"><div id="cp-kicker" class="kicker">Aksar</div>'
        '<div id="cp-title" class="scene-title">Der se ilaaj</div></div>'
        '<div class="duo">'
        f'<div id="cp-a" class="duo-card duo-warn">{icon("warning", "duo-ico", ident="cp-ico-a")}'
        '<div class="duo-title">Complication</div><div class="duo-sub">takleef badhne par</div></div>'
        '<div class="duo-arrow"><div id="cp-arrow" class="arrow-line"></div></div>'
        f'<div id="cp-b" class="duo-card">{icon("doctor", "duo-ico", ident="cp-ico-b")}'
        f'{icon("stethoscope", "duo-ico-sm", ident="cp-ico-c")}'
        '<div class="duo-title">Tabhi doctor ke paas</div><div class="duo-sub">jabki shuruaat mein aana chahiye</div></div>'
        "</div></div>"
    )
    return scene("broll-complication", T["comp_in"], T["comp_out"] + 0.45, 6, 20, broll_inner("broll-complication", inner), ["Full-frame scenes", "Morning", "Complication"])


def takeaway_panel():
    checks = [("salad", "Khaan-paan ka parhez", "saada, kam teekha, kam tala"), ("yoga", "Aahaar-vihaar ka parhez", "sahi dincharya, samay par neend")]
    body = "".join(
        f'<div id="tk-row-{i}" class="row">'
        f'<div class="row-disc">{icon(ic, "row-ico", ident=f"tk-ico-{i}")}</div>'
        f'<div class="row-grow"><div class="row-title">{esc(t)}</div><div class="row-sub">{esc(s)}</div></div>'
        f'{icon("check" if i == 0 else "check-2", "row-check", ident=f"tk-check-{i}")}</div>'
        for i, (ic, t, s) in enumerate(checks)
    )
    inner = (
        '<div id="tk-panel" class="panel">'
        '<div class="panel-head"><div class="kicker">Bachaav</div>'
        '<div class="panel-title">Parhez hi pehla ilaaj</div></div>'
        f'<div class="rows rows-tight">{body}</div>'
        '<div id="tk-result" class="result">'
        f'{icon("sparkles", "result-ico", ident="tk-spark")}'
        '<div><div id="tk-result-1" class="result-a">Piles kam ho sakte hain</div>'
        '<div id="tk-result-2" class="result-b">shuruaat mein hi durust</div></div></div>'
        "</div>"
    )
    return scene("panel-takeaway", T["take_in"], T["take_out"] + 0.5, 5, 20, inner, ["Split-screen panels"])


def end_card():
    inner = (
        '<div id="ec-wrap" class="scene scene-end">'
        + decor("ec", "SAIKRUPA")
        + '<div class="ec-main">'
        '<div id="ec-kicker" class="kicker">Salah ke liye milein</div>'
        '<div id="ec-name" class="ec-name">Dr. Mohan Padole</div>'
        '<div id="ec-cred" class="ec-cred">BAMS, MD</div>'
        f'<div id="ec-clinic" class="ec-clinic">{icon("hospital", "ec-herb")}'
        "<div><div>Saikrupa Ayurvedic Clinic</div><div class=\"ec-city\">Nagpur</div></div></div>"
        '<div id="ec-cta" class="ec-cta">Lakshan dikhein to der na karein, doctor se salah lein.</div>'
        "</div>"
        f'<div id="ec-art" class="ec-art">{icon("stethoscope", "ec-steth")}{icon("herb", "ec-leaf")}</div>'
        '<div id="ec-disclaimer" class="ec-disclaimer">Yeh video sirf jaankari ke liye hai. '
        "Kisi bhi ilaaj se pehle apne doctor se salah lein.</div>"
        "</div>"
    )
    return scene("endcard", END_CARD_IN, TOTAL, 7, 40, broll_inner("endcard", inner), ["Full-frame scenes", "End card"])


CAPTION_CHUNKS = []


def captions():
    live = [(p, page) for p, page in enumerate(PAGES) if min(page["end"], END_CARD_IN) > page["start"]]
    n = len(live)
    parts = 3
    bounds = [round(i * n / parts) for i in range(parts + 1)]
    widx = 0
    for c in range(parts):
        chunk = live[bounds[c]:bounds[c + 1]]
        cid = f"captions-{c + 1}"
        c0 = chunk[0][1]["start"]
        c1 = min(chunk[-1][1]["end"], END_CARD_IN)
        out = []
        for p, page in chunk:
            spans = []
            for w in page["words"]:
                cls = "w key" if w["key"] else "w"
                spans.append(f'<span id="w-{widx}" class="{cls}" data-on="0">{esc(w["text"])}</span>')
                w["_id"] = f"w-{widx}"
                widx += 1
            pend = min(page["end"], END_CARD_IN)
            page["_end"] = pend
            out.append(f'<div id="cap-{p:02d}" class="cap-page"><div id="cap-{p:02d}-in" class="cap-inner">{" ".join(spans)}</div></div>')
        scene(cid, c0, c1, 8, 50, "\n        ".join(out), ["Captions"])
        CAPTION_CHUNKS.append((cid, chunk))


# ---------------------------------------------------------------- audio
SFX = []


def sfx(name, t, vol, lead=0.0):
    SFX.append((name, round(max(0.0, t - lead), 3), vol))


LEADS = {"whoosh": 0.16, "whoosh-short": 0.16, "pop": 0.11, "chime": 0.42, "sparkle": 0.03, "click-soft": 0.06, "ping": 0.32}
DURS = {"whoosh": 0.57, "whoosh-short": 0.57, "pop": 0.72, "chime": 2.5, "sparkle": 1.8, "click-soft": 0.37, "ping": 1.32}


def audio_tags():
    music_auto = {
        "version": 1,
        "lanes": [{
            "target": "volume",
            "points": [
                {"t": 0, "v": 0}, {"t": 1.2, "v": 0.28}, {"t": round(END_CARD_IN - 0.4, 2), "v": 0.28},
                {"t": round(END_CARD_IN + 0.6, 2), "v": 0.55}, {"t": round(TOTAL - 1.6, 2), "v": 0.55}, {"t": TOTAL, "v": 0},
            ],
        }],
    }
    # Voiceover carve from hyperframes-audio/scripts/carve.mjs (re-run it after retiming; see build/README.md).
    carve_path = os.path.join(HERE, "music-carve.json")
    carve_attrs = ""
    if os.path.exists(carve_path):
        with open(carve_path) as f:
            carve = json.load(f)
        music_auto["lanes"] = [l for l in carve["data-automation"]["lanes"] if l["target"] != "volume"] + music_auto["lanes"]
        carve_attrs = (
            f"data-fx-carve='{json.dumps(carve['data-fx-carve'], separators=(',', ':'))}' "
            f"data-fx-chain='{json.dumps(carve['data-fx-chain'], separators=(',', ':'))}' "
        )
    tags = [
        f'<audio id="music-bed" src="assets/audio/music-bed.wav" data-audio-group="music" data-start="0" '
        f'data-duration="{TOTAL}" data-track-index="10" {carve_attrs}'
        f"data-automation='{json.dumps(music_auto, separators=(',', ':'))}'></audio>"
    ]
    lanes = []
    for i, (name, t, vol) in enumerate(sorted(SFX, key=lambda x: x[1])):
        lane = next((k for k, free in enumerate(lanes) if free <= t), None)
        if lane is None:
            lanes.append(0.0)
            lane = len(lanes) - 1
        lanes[lane] = t + DURS[name] + 0.01
        tags.append(
            f'<audio id="sfx-{i:02d}-{name}" src="assets/sfx/{name}.mp3" data-audio-group="sfx" data-start="{t}" '
            f'data-duration="{DURS[name]}" data-track-index="{11 + lane}" data-volume="{vol}"></audio>'
        )
    return "\n        ".join(tags)


# ---------------------------------------------------------------- timeline
def timeline_js():
    use("main")

    def add(line):
        JS[CUR[0]].append(line)

    plan = framing_plan()

    # A-roll camera: one framing per segment with a slow drift; the opening question gets a push-in.
    q = SEGS[0]
    qdur = SEGS[1]["out_start"]
    add(f'tl.fromTo("#cam", {{scale: 1, x: 0, y: 0}}, {{scale: 1.06, x: {-1050 * 0.06:.1f}, y: {-330 * 0.06:.1f}, duration: {qdur - 0.3:.2f}, ease: "none"}}, 0);')
    tq = SEGS[1]["out_start"]
    add(f'tl.to("#cam", {{scale: 1.14, x: {-1050 * 0.14:.1f}, y: {-330 * 0.14:.1f}, duration: 0.3, ease: "power2.in"}}, {tq - 0.3:.2f});')
    add(f'tl.fromTo("#cam-frame", {{filter: "blur(0px)"}}, {{filter: "blur(10px)", duration: 0.3, ease: "power2.in"}}, {tq - 0.3:.2f});')
    add(f'tl.fromTo("#cam-frame", {{filter: "blur(10px)"}}, {{filter: "blur(0px)", duration: 0.45, ease: "power3.out", immediateRender: false}}, {tq:.2f});')
    for i, s in enumerate(SEGS):
        if i == 0:
            continue
        dur = s["src_out"] - s["src_in"]
        a, b = cam_state(plan[i]), cam_state(plan[i], 1.018)
        if i == 1:
            a = {"scale": 1.2, "x": round(960 - 960 * 1.2, 1), "y": round(540 - 540 * 1.2, 1)}
            add(f'tl.fromTo("#cam", {json.dumps(a)}, {{...{json.dumps(cam_state("W"))}, duration: 0.6, ease: "power3.out", immediateRender: false}}, {s["out_start"]});')
            a = cam_state("W")
            add(f'tl.fromTo("#cam", {json.dumps(a)}, {{...{json.dumps(cam_state("W", 1.018))}, duration: {max(0.1, dur - 0.6):.3f}, ease: "none", immediateRender: false}}, {s["out_start"] + 0.6:.3f});')
            continue
        add(f'tl.fromTo("#cam", {json.dumps(a)}, {{...{json.dumps(b)}, duration: {dur:.3f}, ease: "none", immediateRender: false}}, {s["out_start"]});')

    # Split-screen: shift the whole camera left while a panel slides in on the right.
    for a, b in SPLITS:
        add(f'tl.to("#cam-split", {{x: -190, scale: 1.17, duration: 0.6, ease: "power3.inOut"}}, {a});')
        add(f'tl.to("#cam-split", {{x: 0, scale: 1, duration: 0.55, ease: "power3.inOut"}}, {b});')

    use("hook")
    # Hook title.
    h0, h1 = T["hook_in"], T["hook_out"]
    add(f'tl.fromTo("#hook-scrim", {{opacity: 0}}, {{opacity: 1, duration: 0.5}}, {h0});')
    add(f'tl.fromTo("#hook-kicker", {{y: 18, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.4, ease: "power3.out"}}, {h0 + 0.05:.2f});')
    add(f'tl.fromTo("#hook-title", {{y: 50, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.6, ease: "expo.out"}}, {h0 + 0.15:.2f});')
    add(f'tl.fromTo("#hook-rule", {{scaleX: 0}}, {{scaleX: 1, duration: 0.5, ease: "power4.out"}}, {h0 + 0.45:.2f});')
    add(f'tl.fromTo("#hook-sub", {{x: -30, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.5, ease: "power3.out"}}, {h0 + 0.55:.2f});')
    add(f'tl.to("#hook-wrap", {{y: -30, opacity: 0, duration: 0.35, ease: "power2.in"}}, {h1 - 0.4:.2f});')
    sfx("whoosh-short", h0 + 0.15, 0.35)
    sfx("whoosh", tq, 0.55, LEADS["whoosh"])

    use("lower-third")
    # Lower third (opposing clip-path wipes, after the registry's lt-stack-bars).
    l0, l1 = T["lt_in"], T["lt_out"]
    add(f'tl.fromTo("#lt-namebar", {{clipPath: "inset(0 100% 0 0)"}}, {{clipPath: "inset(0 0% 0 0)", duration: 0.55, ease: "power4.out"}}, {l0});')
    add(f'tl.fromTo("#lt-rolebar", {{clipPath: "inset(0 0 0 100%)"}}, {{clipPath: "inset(0 0 0 0%)", duration: 0.55, ease: "power4.out"}}, {l0 + 0.22:.2f});')
    add(f'tl.fromTo("#lt-cred", {{scale: 0.4, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.45, ease: "back.out(2.2)"}}, {l0 + 0.4:.2f});')
    add(f'tl.to("#lt-rolebar", {{clipPath: "inset(0 0 0 100%)", duration: 0.32, ease: "power3.in"}}, {l1:.2f});')
    add(f'tl.to("#lt-namebar", {{clipPath: "inset(0 100% 0 0)", duration: 0.36, ease: "power3.in"}}, {l1 + 0.08:.2f});')
    sfx("click-soft", l0 + 0.05, 0.4, LEADS["click-soft"])

    # Callouts.
    def callout_js(ident, t0, t1, lines_at):
        use(ident)
        add(f'tl.fromTo("#{ident}-card", {{scale: 0.7, y: 20, opacity: 0}}, {{scale: 1, y: 0, opacity: 1, duration: 0.45, ease: "back.out(1.8)"}}, {t0});')
        add(f'tl.fromTo("#{ident}-ico", {{scale: 0.3, rotation: -25}}, {{scale: 1, rotation: 0, duration: 0.6, ease: "back.out(2.6)"}}, {t0 + 0.1:.2f});')
        for i, tt in enumerate(lines_at):
            add(f'tl.fromTo("#{ident}-l{i}", {{x: 24, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.35, ease: "power3.out"}}, {tt:.2f});')
        add(f'tl.to("#{ident}-card", {{scale: 0.92, opacity: 0, duration: 0.3, ease: "power2.in"}}, {t1 - 0.32:.2f});')
        sfx("pop", t0 + 0.05, 0.45, LEADS["pop"])

    callout_js("callout-food", T["food_in"], T["habits_in"] + 0.08, [T["food_in"] + 0.2, T["food_word"]])
    callout_js("callout-sharm", T["sharm_in"], T["sharm_out"], [T["sharm_in"] + 0.2, T["sharm_der"]])

    # Full-frame B-roll: saffron bar wipe in / out.
    def broll_in_out(ident, t0, t1=None):
        add(f'tl.fromTo("#{ident}-in", {{clipPath: "inset(0 0 0 100%)"}}, {{clipPath: "inset(0 0 0 0%)", duration: 0.5, ease: "power3.inOut"}}, {t0});')
        add(f'tl.fromTo("#{ident}-bar", {{xPercent: 0}}, {{xPercent: -1600, duration: 0.5, ease: "power3.inOut"}}, {t0});')
        add(f'tl.to("#{ident}-bar", {{xPercent: -1800, duration: 0.15, ease: "power1.in"}}, {t0 + 0.5:.2f});')
        sfx("whoosh", t0 + 0.2, 0.5, LEADS["whoosh"])
        if t1 is not None:
            add(f'tl.to("#{ident}-in", {{clipPath: "inset(0 100% 0 0)", duration: 0.45, ease: "power3.inOut"}}, {t1});')
            sfx("whoosh-short", t1 + 0.18, 0.3, LEADS["whoosh-short"])

    def scene_head(prefix, t0):
        add(f'tl.fromTo("#{prefix}-kicker", {{y: 16, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.4, ease: "power3.out"}}, {t0 + 0.35:.2f});')
        add(f'tl.fromTo("#{prefix}-title", {{y: 40, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.6, ease: "expo.out"}}, {t0 + 0.42:.2f});')

    def ambient(prefix, t0, t1):
        d = round(t1 - t0, 2)
        add(f'tl.fromTo("#{prefix}-ghost", {{x: 60}}, {{x: -140, duration: {d}, ease: "none"}}, {t0});')
        add(f'tl.fromTo("#{prefix}-glow-a", {{scale: 0.9, opacity: 0.55}}, {{scale: 1.15, opacity: 0.9, duration: {d}, ease: "sine.inOut"}}, {t0});')
        add(f'tl.fromTo("#{prefix}-glow-b", {{scale: 1.1, x: 0}}, {{scale: 0.95, x: -80, duration: {d}, ease: "sine.inOut"}}, {t0});')

    # Habits.
    use("broll-habits")
    a, b = T["habits_in"], T["habits_out"]
    broll_in_out("broll-habits", a, b)
    scene_head("hab", a)
    ambient("hab", a, b + 0.45)
    t_raat = at("raat")
    add(f'tl.fromTo("#hab-sleep", {{y: 60, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.6, ease: "power3.out"}}, {t_raat:.2f});')
    add(f'tl.fromTo(".sleep-moon", {{rotation: -30, scale: 0.5}}, {{rotation: 0, scale: 1, duration: 0.8, ease: "back.out(2)"}}, {t_raat + 0.1:.2f});')
    add(f'tl.fromTo(".sleep-phone", {{y: 40, rotation: 12, opacity: 0}}, {{y: 0, rotation: 6, opacity: 1, duration: 0.6, ease: "power3.out"}}, {t_raat + 0.35:.2f});')
    add(f'tl.fromTo(".sleep-time", {{opacity: 0}}, {{opacity: 1, duration: 0.3}}, {t_raat + 0.5:.2f});')
    sfx("pop", t_raat + 0.05, 0.35, LEADS["pop"])
    for i, wd in enumerate(["masaledaar", "tez", "teekha", "tala"]):
        tt = at(wd)
        add(f'tl.fromTo("#hab-food-{i}", {{scale: 0.6, y: 40, opacity: 0}}, {{scale: 1, y: 0, opacity: 1, duration: 0.45, ease: "back.out(1.9)"}}, {tt - 0.05:.2f});')
        add(f'tl.fromTo("#hab-food-{i} .food-ico", {{rotation: -20, scale: 0.5}}, {{rotation: 0, scale: 1, duration: 0.55, ease: "back.out(2.4)"}}, {tt:.2f});')
        sfx("pop", tt, 0.32, LEADS["pop"])
    tm = at("mirchi")
    add(f'tl.fromTo("#hab-food-2", {{scale: 1}}, {{scale: 1.07, duration: 0.18, ease: "power2.out", yoyo: true, repeat: 1, immediateRender: false}}, {tm:.2f});')

    # Cause -> effect chain (split screen).
    use("panel-chain")
    a, b = T["chain_in"], T["chain_out"]
    add(f'tl.fromTo("#ch-panel", {{xPercent: 115}}, {{xPercent: 0, duration: 0.65, ease: "power3.out"}}, {a});')
    add(f'tl.to("#ch-panel", {{xPercent: 115, duration: 0.5, ease: "power3.in"}}, {b});')
    sfx("whoosh", a + 0.15, 0.45, LEADS["whoosh"])
    sfx("whoosh-short", b + 0.15, 0.3, LEADS["whoosh-short"])
    steps = T["chain_steps"]
    for i, tt in enumerate(steps):
        add(f'tl.fromTo("#ch-row-{i}", {{opacity: 0.22, x: 30}}, {{opacity: 1, x: 0, duration: 0.45, ease: "power3.out"}}, {tt:.2f});')
        add(f'tl.fromTo("#ch-ico-{i}", {{scale: 0.4}}, {{scale: 1, duration: 0.55, ease: "back.out(2.4)", immediateRender: false}}, {tt:.2f});')
        add(f'tl.to("#ch-row-{i} .row-disc", {{backgroundColor: "#F7C873", duration: 0.3}}, {tt:.2f});')
        sfx("click-soft" if i < 3 else "ping", tt + 0.02, 0.45 if i < 3 else 0.3, LEADS["click-soft" if i < 3 else "ping"])
        if i > 0:
            add(f'tl.to("#ch-rail-fill", {{scaleY: {i / 3:.3f}, duration: 0.45, ease: "power2.inOut"}}, {tt - 0.15:.2f});')
    add('tl.set("#ch-rail-fill", {scaleY: 0}, 0);')
    add(f'tl.fromTo("#ch-row-3", {{scale: 1}}, {{scale: 1.05, duration: 0.25, yoyo: true, repeat: 1, ease: "power2.out", immediateRender: false}}, {steps[3] + 0.45:.2f});')

    # Morning pain.
    use("broll-morning")
    a, b = T["morning_in"], T["morning_out"]
    broll_in_out("broll-morning", a, b)
    scene_head("mo", a)
    ambient("mo", a, b + 0.45)
    for i, tt in enumerate(T["morning_steps"]):
        add(f'tl.fromTo("#mo-step-{i}", {{y: 70, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.55, ease: "power3.out"}}, {tt - 0.05:.2f});')
        add(f'tl.fromTo("#mo-ico-{i}", {{scale: 0.4, rotation: -15}}, {{scale: 1, rotation: 0, duration: 0.6, ease: "back.out(2.2)"}}, {tt:.2f});')
        sfx("pop", tt, 0.32, LEADS["pop"])
        if i > 0:
            add(f'tl.fromTo("#mo-arrow-{i - 1}", {{scaleX: 0}}, {{scaleX: 1, duration: 0.4, ease: "power2.out"}}, {tt - 0.3:.2f});')
    tp = T["morning_pain"]
    add(f'tl.to("#mo-step-2", {{backgroundColor: "#173F35", duration: 0.35}}, {tp:.2f});')
    add(f'tl.to("#mo-step-2 .step-title, #mo-step-2 .step-num", {{color: "#FBF4E6", duration: 0.35}}, {tp:.2f});')
    add(f'tl.to("#mo-step-2 .step-sub", {{color: "#F7C873", duration: 0.35}}, {tp:.2f});')
    add(f'tl.fromTo("#mo-ico-2", {{x: 0}}, {{x: 6, duration: 0.06, yoyo: true, repeat: 5, ease: "none", immediateRender: false}}, {tp:.2f});')

    # Complication -> doctor.
    use("broll-complication")
    a, b = T["comp_in"], T["comp_out"]
    broll_in_out("broll-complication", a, b)
    scene_head("cp", a)
    ambient("cp", a, b + 0.45)
    c0, c1 = T["comp_steps"]
    add(f'tl.fromTo("#cp-a", {{x: -80, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.55, ease: "power3.out"}}, {c0 - 0.05:.2f});')
    add(f'tl.fromTo("#cp-ico-a", {{scale: 0.4}}, {{scale: 1, duration: 0.6, ease: "back.out(2.4)"}}, {c0:.2f});')
    add(f'tl.fromTo("#cp-arrow", {{scaleX: 0}}, {{scaleX: 1, duration: 0.5, ease: "power2.out"}}, {c1 - 0.45:.2f});')
    add(f'tl.fromTo("#cp-b", {{x: 80, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.55, ease: "power3.out"}}, {c1 - 0.05:.2f});')
    add(f'tl.fromTo("#cp-ico-b", {{scale: 0.4}}, {{scale: 1, duration: 0.6, ease: "back.out(2.4)"}}, {c1:.2f});')
    add(f'tl.fromTo("#cp-ico-c", {{scale: 0, rotation: -40}}, {{scale: 1, rotation: 0, duration: 0.6, ease: "back.out(2.4)"}}, {c1 + 0.2:.2f});')
    sfx("pop", c0, 0.35, LEADS["pop"])
    sfx("pop", c1, 0.35, LEADS["pop"])

    # Takeaway (split screen).
    use("panel-takeaway")
    a, b = T["take_in"], T["take_out"]
    add(f'tl.fromTo("#tk-panel", {{xPercent: 115}}, {{xPercent: 0, duration: 0.65, ease: "power3.out"}}, {a});')
    sfx("whoosh", a + 0.15, 0.45, LEADS["whoosh"])
    k0, k1, k2, k3 = T["take_steps"]
    for i, tt in enumerate([k0, k1]):
        add(f'tl.fromTo("#tk-row-{i}", {{y: 40, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.5, ease: "power3.out"}}, {tt - 0.1:.2f});')
        add(f'tl.fromTo("#tk-ico-{i}", {{scale: 0.4}}, {{scale: 1, duration: 0.55, ease: "back.out(2.4)"}}, {tt:.2f});')
        add(f'tl.fromTo("#tk-check-{i}", {{scale: 0, rotation: -30}}, {{scale: 1, rotation: 0, duration: 0.45, ease: "back.out(3)"}}, {tt + 0.6:.2f});')
        sfx("pop", tt, 0.32, LEADS["pop"])
        sfx("click-soft", tt + 0.65, 0.4, LEADS["click-soft"])
    add(f'tl.fromTo("#tk-result", {{y: 50, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.55, ease: "power3.out"}}, {k2 - 0.1:.2f});')
    add(f'tl.fromTo("#tk-result-2", {{opacity: 0, x: -20}}, {{opacity: 1, x: 0, duration: 0.45, ease: "power3.out"}}, {k3 - 0.05:.2f});')
    add(f'tl.fromTo("#tk-spark", {{scale: 0.3, rotation: -40}}, {{scale: 1, rotation: 0, duration: 0.7, ease: "back.out(2.6)"}}, {k3:.2f});')
    sfx("chime", k3, 0.4, LEADS["chime"])

    # End card.
    use("endcard")
    e0 = END_CARD_IN
    broll_in_out("endcard", e0)
    ambient("ec", e0, TOTAL)
    add(f'tl.fromTo("#ec-kicker", {{y: 16, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.4, ease: "power3.out"}}, {e0 + 0.45:.2f});')
    add(f'tl.fromTo("#ec-name", {{y: 50, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.7, ease: "expo.out"}}, {e0 + 0.55:.2f});')
    add(f'tl.fromTo("#ec-cred", {{scale: 0.4, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.5, ease: "back.out(2.2)"}}, {e0 + 0.9:.2f});')
    add(f'tl.fromTo("#ec-clinic", {{x: -40, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.5, ease: "power3.out"}}, {e0 + 1.1:.2f});')
    add(f'tl.fromTo("#ec-cta", {{y: 30, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.5, ease: "power3.out"}}, {e0 + 1.6:.2f});')
    add(f'tl.fromTo("#ec-art", {{scale: 0.6, rotation: -12, opacity: 0}}, {{scale: 1, rotation: 0, opacity: 1, duration: 0.9, ease: "back.out(1.7)"}}, {e0 + 0.7:.2f});')
    add(f'tl.to("#ec-art", {{y: -18, duration: {TOTAL - e0 - 1.6:.2f}, ease: "sine.inOut"}}, {e0 + 1.6:.2f});')
    add(f'tl.fromTo("#ec-disclaimer", {{opacity: 0}}, {{opacity: 1, duration: 0.6}}, {e0 + 2.0:.2f});')
    sfx("sparkle", e0 + 0.9, 0.3, LEADS["sparkle"])

    # Captions: page entrance + per-word highlight.
    for cid, chunk in CAPTION_CHUNKS:
      use(cid)
      for p, page in chunk:
        add(f'tl.set("#cap-{p:02d}", {{autoAlpha: 1}}, {page["start"]});')
        add(f'tl.set("#cap-{p:02d}", {{autoAlpha: 0}}, {page["_end"]:.3f});')
        add(f'tl.fromTo("#cap-{p:02d}-in", {{y: 14, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.14, ease: "power2.out"}}, {page["start"]});')
        for w in page["words"]:
            add(f'tl.set("#{w["_id"]}", {{attr: {{"data-on": "1"}}}}, {w["start"]});')
            add(f'tl.set("#{w["_id"]}", {{attr: {{"data-on": "0"}}}}, {max(w["end"], w["start"] + 0.12):.3f});')


CSS = r"""
      @font-face { font-family: "Fraunces"; src: url("assets/fonts/fraunces-latin-full.woff2") format("woff2"); font-weight: 100 900; }
      @font-face { font-family: "Montserrat"; src: url("assets/fonts/montserrat-latin-wght.woff2") format("woff2"); font-weight: 100 900; }
      :root {
        --cream: #fbf4e6; --cream-2: #f3e7cf; --line: #e2d1ae; --green: #173f35; --green-2: #24584a;
        --saffron: #e8962e; --saffron-soft: #f7c873; --saffron-deep: #9a4f0e; --ink: #13261f; --muted: #50645b;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #0d1714; }
      body { font-family: "Montserrat", sans-serif; color: var(--ink); }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #0d1714; }
      #cam-frame { position: absolute; inset: 0; overflow: hidden; }
      #cam-split, #cam { position: absolute; inset: 0; transform-origin: 0 0; }
      #cam-split { transform-origin: 680px 420px; }
      .aroll { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }

      /* Shared type */
      .kicker { display: inline-block; font: 800 22px/1 "Montserrat"; letter-spacing: 0.16em; text-transform: uppercase;
        color: var(--saffron-deep); padding: 10px 16px; border: 2px solid var(--saffron); border-radius: 999px; }
      .kicker-solid { background: var(--saffron-soft); border-color: var(--saffron-soft); color: var(--ink); }
      .ico { display: block; width: 160px; height: 160px; object-fit: contain; }

      /* Hook */
      .hook { position: absolute; left: 96px; top: 96px; width: 760px; }
      .hook-scrim { position: absolute; left: -300px; top: -260px; width: 1150px; height: 820px;
        background: radial-gradient(closest-side, rgba(9, 20, 16, 0.78), rgba(9, 20, 16, 0.45) 55%, rgba(9, 20, 16, 0)); }
      .hook > :not(.hook-scrim) { position: relative; }
      .hook-title { margin-top: 26px; font: 700 100px/0.95 "Fraunces"; color: var(--cream); letter-spacing: -0.02em; }
      .hook-rule { width: 260px; height: 8px; margin: 26px 0 22px; background: var(--saffron); border-radius: 4px; transform-origin: 0 50%; }
      .hook-sub { font: 700 44px/1.1 "Montserrat"; color: var(--saffron-soft); }

      /* Lower third */
      .lt { position: absolute; left: 96px; bottom: 196px; display: flex; flex-direction: column; align-items: flex-start; gap: 10px; }
      .lt-namebar { display: flex; align-items: center; gap: 22px; background: var(--green); padding: 18px 26px 18px 32px; border-radius: 14px; }
      .lt-name { font: 700 58px/1 "Fraunces"; color: var(--cream); white-space: nowrap; }
      .lt-cred { display: block; font: 800 24px/1 "Montserrat"; color: var(--ink); background: var(--saffron-soft); padding: 10px 14px; border-radius: 10px; letter-spacing: 0.06em; }
      .lt-rolebar { display: flex; align-items: center; gap: 14px; margin-left: 18px; background: var(--cream); padding: 12px 24px 12px 14px;
        border-radius: 12px; font: 700 30px/1 "Montserrat"; color: var(--green); white-space: nowrap; }
      .lt-ico { width: 46px; height: 46px; }

      /* Callouts */
      .callout { position: absolute; right: 300px; top: 110px; display: flex; align-items: center; gap: 24px; background: var(--cream);
        border: 3px solid var(--saffron); border-radius: 28px; padding: 22px 40px 22px 22px; box-shadow: 0 24px 60px rgba(0,0,0,0.35); }
      .co-ico-wrap { width: 150px; height: 150px; border-radius: 50%; background: var(--cream-2); display: flex; align-items: center; justify-content: center; }
      .co-ico { width: 124px; height: 124px; }
      .co-label { font: 800 22px/1 "Montserrat"; letter-spacing: 0.16em; text-transform: uppercase; color: var(--saffron-deep); margin-bottom: 12px; }
      .co-line { font: 700 50px/1.12 "Fraunces"; color: var(--green); white-space: nowrap; }
      .co-line + .co-line { font: 700 34px/1.2 "Montserrat"; color: var(--muted); margin-top: 6px; }

      /* Full-frame scenes */
      .broll, .broll-in { position: absolute; inset: 0; overflow: hidden; }
      .scene { position: absolute; inset: 0; background: var(--cream); overflow: hidden; }
      .scene > * { position: absolute; }
      .bg-dots { inset: 0; background-image: radial-gradient(rgba(23, 63, 53, 0.13) 2px, transparent 2.5px); background-size: 34px 34px; }
      .glow { border-radius: 50%; }
      .glow-a { width: 900px; height: 900px; right: -220px; top: -320px; background: radial-gradient(closest-side, rgba(232,150,46,0.30), rgba(232,150,46,0)); }
      .glow-b { width: 1000px; height: 1000px; left: -380px; bottom: -520px; background: radial-gradient(closest-side, rgba(36,88,74,0.20), rgba(36,88,74,0)); }
      .ghost { right: -40px; bottom: 120px; font: 900 300px/1 "Fraunces"; color: rgba(23, 63, 53, 0.08); white-space: nowrap; letter-spacing: -0.02em; }
      .scene-head { left: 120px; top: 84px; }
      .scene-title { margin-top: 18px; font: 700 86px/1 "Fraunces"; color: var(--green); letter-spacing: -0.01em; }
      .wipe-bar { position: absolute; top: 0; bottom: 0; left: 100%; width: 120px; background: var(--saffron); z-index: 30; }

      /* Habits */
      .sleep-card { left: 120px; top: 300px; width: 620px; height: 540px; background: var(--green); border-radius: 36px; padding: 44px 48px; color: var(--cream); }
      .sleep-icons { position: relative; height: 210px; }
      .sleep-moon { position: absolute; left: 0; top: 0; width: 210px; height: 210px; }
      .sleep-phone { position: absolute; left: 150px; top: 76px; width: 130px; height: 130px; }
      .sleep-time { position: absolute; right: 48px; top: 60px; font: 800 44px/1 "Montserrat"; color: var(--saffron-soft); font-variant-numeric: tabular-nums; }
      .sleep-title { margin-top: 44px; font: 700 64px/1.02 "Fraunces"; }
      .sleep-sub { margin-top: 16px; font: 700 32px/1 "Montserrat"; color: var(--saffron-soft); }
      .food-grid { left: 800px; top: 300px; width: 1000px; height: 540px; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 28px; }
      .food-card { display: flex; align-items: center; gap: 22px; background: #fffaf0; border: 3px solid var(--line); border-radius: 28px; padding: 22px 26px; }
      .food-ico { width: 150px; height: 150px; flex: none; }
      .food-title { font: 800 40px/1.05 "Montserrat"; color: var(--green); }
      .food-sub { margin-top: 10px; font: 600 26px/1 "Montserrat"; color: var(--saffron-deep); }

      /* Split-screen panels */
      .panel { position: absolute; left: 950px; top: 70px; width: 900px; height: 780px; background: var(--cream); border-radius: 36px;
        padding: 46px 52px; box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4); overflow: hidden; }
      .panel-head { margin-bottom: 30px; }
      .panel-title { margin-top: 16px; font: 700 62px/1.02 "Fraunces"; color: var(--green); }
      .rows { position: relative; display: flex; flex-direction: column; gap: 22px; }
      .rows-tight { gap: 20px; }
      .rail { position: absolute; left: 54px; top: 54px; bottom: 54px; width: 6px; background: var(--line); border-radius: 3px; }
      .rail-fill { width: 100%; height: 100%; background: var(--saffron); border-radius: 3px; transform-origin: 50% 0; }
      .row { position: relative; display: flex; align-items: center; gap: 26px; }
      .row-disc { width: 108px; height: 108px; border-radius: 50%; background: var(--cream-2); border: 3px solid var(--line); display: flex; align-items: center; justify-content: center; flex: none; }
      .row-ico { width: 82px; height: 82px; }
      .row-grow { flex: 1; }
      .row-title { font: 800 40px/1.08 "Montserrat"; color: var(--green); }
      .row-sub { margin-top: 8px; font: 600 26px/1.1 "Montserrat"; color: var(--muted); }
      .row-check { width: 72px; height: 72px; }
      #ch-panel .row { opacity: 0.22; }
      .result { display: flex; align-items: center; gap: 22px; margin-top: 34px; background: var(--green); border-radius: 26px; padding: 26px 30px; color: var(--cream); }
      .result-ico { width: 96px; height: 96px; flex: none; }
      .result-a { font: 700 48px/1.05 "Fraunces"; }
      .result-b { margin-top: 10px; font: 800 32px/1 "Montserrat"; color: var(--saffron-soft); }

      /* Morning */
      .steps { left: 120px; right: 120px; top: 330px; display: flex; align-items: stretch; }
      .step { width: 470px; height: 470px; background: #fffaf0; border: 3px solid var(--line); border-radius: 36px; padding: 36px 40px; }
      .step-ico { width: 170px; height: 170px; }
      .step-num { margin-top: 18px; font: 800 26px/1 "Montserrat"; color: var(--saffron-deep); letter-spacing: 0.1em; }
      .step-title { margin-top: 12px; font: 700 52px/1.04 "Fraunces"; color: var(--green); }
      .step-sub { margin-top: 12px; font: 600 28px/1.1 "Montserrat"; color: var(--muted); }
      .arrow { flex: 1; display: flex; align-items: center; padding: 0 18px; }
      .arrow-line { width: 100%; height: 8px; background: var(--saffron); border-radius: 4px; transform-origin: 0 50%; position: relative; }
      .arrow-line::after { content: ""; position: absolute; right: -4px; top: -12px; border-left: 22px solid var(--saffron); border-top: 16px solid transparent; border-bottom: 16px solid transparent; }

      /* Complication */
      .duo { left: 120px; right: 120px; top: 320px; display: flex; align-items: center; }
      .duo-card { position: relative; width: 680px; height: 480px; background: #fffaf0; border: 3px solid var(--line); border-radius: 36px; padding: 44px 48px; }
      .duo-warn { border-color: var(--saffron); }
      .duo-ico { width: 190px; height: 190px; }
      .duo-ico-sm { position: absolute; left: 190px; top: 120px; width: 120px; height: 120px; }
      .duo-title { margin-top: 30px; font: 700 64px/1.02 "Fraunces"; color: var(--green); }
      .duo-sub { margin-top: 14px; font: 600 30px/1.1 "Montserrat"; color: var(--muted); }
      .duo-arrow { flex: 1; padding: 0 30px; }

      /* End card */
      .scene-end .ec-main { left: 120px; top: 150px; width: 1100px; }
      .ec-name { margin-top: 30px; font: 700 120px/0.98 "Fraunces"; color: var(--green); letter-spacing: -0.02em; }
      .ec-cred { display: inline-block; margin-top: 26px; font: 800 34px/1 "Montserrat"; color: var(--ink); background: var(--saffron-soft); padding: 14px 20px; border-radius: 12px; letter-spacing: 0.06em; }
      .ec-clinic { display: flex; align-items: center; gap: 22px; margin-top: 40px; font: 700 50px/1.1 "Fraunces"; color: var(--green); }
      .ec-city { font: 700 32px/1.2 "Montserrat"; color: var(--saffron-deep); margin-top: 6px; }
      .ec-herb { width: 110px; height: 110px; }
      .ec-cta { margin-top: 48px; font: 700 36px/1.3 "Montserrat"; color: var(--ink); max-width: 1120px; }
      .ec-art { right: 160px; top: 230px; width: 520px; height: 520px; border-radius: 50%; background: var(--green); display: flex; align-items: center; justify-content: center; }
      .ec-steth { width: 300px; height: 300px; }
      .ec-leaf { position: absolute; right: 30px; bottom: 40px; width: 150px; height: 150px; }
      .ec-disclaimer { left: 120px; right: 120px; bottom: 56px; font: 600 26px/1.3 "Montserrat"; color: var(--muted); border-top: 2px solid var(--line); padding-top: 22px; }

      /* Captions */
      .cap-page { position: absolute; left: 0; right: 0; bottom: 84px; display: flex; justify-content: center; z-index: 60; visibility: hidden; }
      .cap-inner { display: flex; flex-wrap: nowrap; gap: 14px; font: 800 60px/1.15 "Montserrat"; color: #fffdf6; white-space: nowrap;
        -webkit-text-stroke: 12px rgba(10, 22, 18, 0.94); paint-order: stroke fill; text-shadow: 0 8px 26px rgba(0, 0, 0, 0.45); }
      .w { display: inline-block; padding: 2px 10px 6px; border-radius: 14px; }
      .w.key { color: #ffd98a; }
      .w[data-on="1"] { background: var(--saffron-soft); color: #16110a; -webkit-text-stroke: 0; text-shadow: none; }
"""


TIME_ARG = re.compile(r", (-?\d+(?:\.\d+)?)\);$")


def localize(lines, t0):
    out = []
    for line in lines:
        m = TIME_ARG.search(line)
        assert m, line
        local = max(0.0, float(m.group(1)) - t0)
        out.append(line[: m.start()] + f", {local:.3f});")
    return out


def css_sections():
    parts = re.split(r"\n\s*/\* (.+?) \*/\n", CSS)
    base = parts[0]
    named = {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}
    fonts = "\n".join(l for l in base.splitlines() if "@font-face" in l)
    root_vars = base[base.index(":root {"): base.index("}", base.index(":root {")) + 1]
    return base, fonts, root_vars, named


def write_subcomp(ident, sc, lines):
    _, fonts, root_vars, named = css_sections()
    css = "\n".join(named[k] for k in ["Shared type"] + sc["css"])
    dur = round(sc["end"] - sc["start"], 3)
    doc = f"""<!doctype html>
<html lang="hi-Latn">
  <head>
    <meta charset="UTF-8" />
    <!-- generated by build/compose.py: edit the generator, then re-run it -->
  </head>
  <body>
    <template>
      <style>
{fonts}
      {root_vars.replace(":root", "#" + ident)}
      #{ident} {{ position: absolute; inset: 0; overflow: hidden; font-family: "Montserrat", sans-serif; color: var(--ink); }}
      #{ident} *, #{ident} *::before, #{ident} *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
{css}
      </style>
      <div id="{ident}" data-composition-id="{ident}" data-width="1920" data-height="1080" data-duration="{dur}">
        {sc["html"]}
      </div>
      <script>
        const tl = gsap.timeline({{ paused: true }});
        {chr(10).join("        " + l for l in localize(lines, sc["start"])).lstrip()}
        window.__timelines["{ident}"] = tl;
      </script>
    </template>
  </body>
</html>
"""
    os.makedirs(os.path.join(ROOT, "compositions"), exist_ok=True)
    with open(os.path.join(ROOT, "compositions", f"{ident}.html"), "w") as f:
        f.write(doc)


def main():
    hook()
    lower_third()
    callout("callout-food", T["food_in"], T["habits_in"] + 0.08, "curry", "Mukhya kaaran", ["Khaan-paan", "aur dincharya"])
    callout("callout-sharm", T["sharm_in"], T["sharm_out"], "hide", "Aksar", ["Sharm ki wajah se", "ilaaj mein der"])
    habits()
    chain_panel()
    morning()
    complication()
    takeaway_panel()
    end_card()
    captions()
    timeline_js()

    hosts = []
    for ident, sc in SCENES.items():
        write_subcomp(ident, sc, JS.get(ident, []))
        hosts.append(
            f'<div id="{ident}" data-composition-id="{ident}" data-composition-src="compositions/{ident}.html" '
            f'data-start="{sc["start"]}" data-duration="{round(sc["end"] - sc["start"], 3)}" '
            f'data-track-index="{sc["track"]}" data-width="1920" data-height="1080" '
            f'style="position: absolute; inset: 0; z-index: {sc["z"]}"></div>'
        )
    base, _, _, _ = css_sections()
    main_js = "\n      ".join(JS["main"])
    doc = f"""<!doctype html>
<html lang="hi-Latn">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Piles &amp; Fissure: Dr. Mohan Padole</title>
    <script src="vendor/gsap.min.js"></script>
    <style>{base}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <!-- generated by build/compose.py: edit the generator, then re-run it -->
      <div id="cam-frame">
        <div id="cam-split" data-layout-allow-overflow>
          <div id="cam" data-layout-allow-overflow>
        {aroll_clips()}
          </div>
        </div>
      </div>
      {chr(10).join("      " + h for h in hosts).lstrip()}
      {audio_tags()}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {main_js}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    with open(os.path.join(ROOT, "index.html"), "w") as f:
        f.write(doc)
    print(f"index.html: {TOTAL}s, {len(SEGS)} A-roll clips, {len(SCENES)} sub-compositions, {len(SFX)} sfx")


if __name__ == "__main__":
    main()
