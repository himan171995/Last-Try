"""Render the A-roll panel (840x980, 30 fps): cut, reframed, graded, plus the cut dialogue.

Usage: python3 -I build/aroll.py SOURCE.mp4
Writes assets/video/aroll.mp4 (picture only), assets/audio/dialog-raw.wav and build/shots.json.
The panel shows near-native resolution crops of the 576x1024 source. Shot changes land on cuts
where a pause was removed (so jump cuts read as camera changes); slow push-ins are added in the
composition.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = sys.argv[1]
PW, PH, FPS = 840, 980, 30
SW, SH = 576, 1024
EDIT = json.load(open(os.path.join(HERE, "edit.json")))
SEGS = EDIT["segments"]
GRADE = ("hqdn3d=1.5:1.5:3:3,colorchannelmixer=rr=0.97:gg=1.0:bb=1.06,"
         "colorbalance=rs=-0.04:gs=0.0:bs=0.05:rm=0.02:bm=-0.02:rh=0.03:bh=-0.03,"
         "curves=master='0/0.03 0.25/0.22 0.5/0.5 0.78/0.81 1/0.97',eq=saturation=1.06")
FACE = {"question": (158, 380), "intro": (170, 372), "shloka": (166, 376), "sukh": (160, 380),
        "stress": (158, 385), "dairy": (150, 374), "grain": (152, 380), "sweets": (150, 380),
        "conclusion": (146, 380)}
PATIENT = (410, 365)
ASPECT = PW / PH


def crop(shot, section):
    if shot == "TWO":
        w = 576
        x, fy = 0, 375
        h = w / ASPECT
        y = fy - 0.33 * h
    else:
        w = {"DOC_M": 400, "DOC_C": 300, "PAT_M": 380}[shot]
        h = w / ASPECT
        fx, fy = PATIENT if shot == "PAT_M" else FACE[section]
        x = fx - (0.55 if shot == "PAT_M" else 0.47) * w
        y = fy - 0.32 * h
    w, h = round(w / 2) * 2, round(h / 2) * 2
    x = min(max(0, round(x)), SW - w)
    y = min(max(0, round(y)), SH - h)
    return w, h, x, y


def plan():
    """One shot per run of segments; change framing at section starts and at removed pauses."""
    cycle = ["DOC_M", "DOC_C", "DOC_M", "TWO"]
    shots, k, cur, cur_start = [], 0, None, 0.0
    prev = None
    for i, s in enumerate(SEGS):
        if s.get("gap"):
            prev = None
            continue
        if s["section"] == "question":
            name = "TWO" if s["src_start"] < 8 else "PAT_M"
        else:
            removed = (s["src_start"] - prev["src_end"]) if prev and prev["section"] == s["section"] else 99
            long_enough = s["out_start"] - cur_start >= 2.4
            if cur in (None, "TWO", "PAT_M") and s["section"] != "question" and (cur is None or prev is None or prev["section"] == "question"):
                name = "DOC_M"
            elif removed > 0.22 and long_enough:
                k += 1
                name = cycle[k % len(cycle)]
            else:
                name = cur
        if name != cur:
            shots.append({"shot": name, "start": s["out_start"], "seg": i})
            cur, cur_start = name, s["out_start"]
        s["shot"] = name
        prev = s
    return shots


def main():
    shots = plan()
    total = 0
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{PW}x{PH}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-g", "30",
         "-movflags", "+faststart", os.path.join(ROOT, "assets/video/aroll.mp4")], stdin=subprocess.PIPE)
    fsz = PW * PH * 3
    for s in SEGS:
        n = s["frames"]
        if s.get("gap"):
            enc.stdin.write(bytes(fsz) * n)
            total += n
            continue
        w, h, x, y = crop(s["shot"], s["section"])
        vf = f"{GRADE},crop={w}:{h}:{x}:{y},scale={PW}:{PH}:flags=lanczos,unsharp=5:5:0.5:5:5:0,fps={FPS}"
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s['src_start']:.3f}", "-i", SRC, "-t",
                              f"{n / FPS + 0.2:.3f}", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        have = len(raw) // fsz
        for k in range(n):
            j = min(k, have - 1)
            enc.stdin.write(raw[j * fsz:(j + 1) * fsz])
        total += n
    enc.stdin.close()
    enc.wait()
    json.dump(shots, open(os.path.join(HERE, "shots.json"), "w"), indent=1)
    print("frames", total, "=", round(total / FPS, 3), "s;", len(shots), "shots")

    parts, labels = [], []
    for i, s in enumerate(SEGS):
        d = s["frames"] / FPS
        if s.get("gap"):
            parts.append(f"anullsrc=r=44100:cl=stereo,atrim=duration={d:.4f}[a{i}]")
        else:
            parts.append(f"[0:a]atrim=start={s['src_start']:.3f}:duration={d:.4f},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d=0.008,afade=t=out:st={d - 0.008:.4f}:d=0.008[a{i}]")
        labels.append(f"[a{i}]")
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(SEGS)}:v=0:a=1,aresample=48000[out]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[out]", "-ac", "1",
                    "-c:a", "pcm_s24le", os.path.join(ROOT, "assets/audio/dialog-raw.wav")], check=True)


if __name__ == "__main__":
    main()
