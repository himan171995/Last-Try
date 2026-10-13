"""Render the A-roll: cut, reframed, graded, upscaled 1080x1920 picture plus the cut dialogue.

Usage: python3 -I build/aroll.py SOURCE.mp4
Writes assets/video/aroll.mp4 (picture only) and assets/audio/dialog.wav.

Each shot is a 9:16 crop of the 576x1024 source framed on a speaker, with a slow push-in.
Shot changes sit on the cuts where pauses were removed, so jump cuts read as camera changes.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = sys.argv[1]
W, H, FPS = 1080, 1920, 30
SW, SH = 576, 1024
EDIT = json.load(open(os.path.join(HERE, "edit.json")))
SEGS = EDIT["segments"]

GRADE = ("hqdn3d=1.5:1.5:3:3,"
         "colorchannelmixer=rr=0.97:gg=1.0:bb=1.06,"
         "colorbalance=rs=-0.04:gs=0.0:bs=0.05:rm=0.02:bm=-0.02:rh=0.03:bh=-0.03,"
         "curves=master='0/0.03 0.25/0.22 0.5/0.5 0.78/0.81 1/0.97',eq=saturation=1.06")

# Speaker face position (source px) per section; the camera barely moves in the source.
FACE = {"question": (158, 380), "charaka": (170, 372), "stress": (158, 385), "dairy": (150, 374),
        "grain": (152, 380), "sweets": (150, 380), "conclusion": (146, 380)}
PATIENT_FACE = (410, 365)

# name -> (crop width, face height within crop, face x within crop or None for fixed centre)
SHOTS = {
    "TWO": (480, None, None),
    "PAT_M": (360, 0.31, 0.55),
    "DOC_M": (400, 0.31, None),
    "DOC_M2": (356, 0.31, 0.46),
    "DOC_C": (300, 0.32, 0.48),
}
# (first segment, last segment, shot, push-in amount)
PLAN = [
    (0, 1, "TWO", 0.10), (2, 3, "PAT_M", 0.06),
    (4, 4, "DOC_M", 0.03), (5, 6, "DOC_M2", 0.04), (7, 7, "DOC_C", 0.02),
    (8, 10, "DOC_M", 0.06), (11, 13, "DOC_C", 0.04), (14, 14, "DOC_M2", 0.03),
    (15, 20, "DOC_M", 0.08),
    (21, 23, "DOC_C", 0.05), (24, 26, "DOC_M", 0.04), (27, 27, "DOC_C", 0.02),
    (28, 28, "DOC_M", 0.02), (29, 29, "DOC_C", 0.03), (30, 33, "DOC_M2", 0.06),
    (34, 34, "DOC_M", 0.02), (35, 36, "DOC_C", 0.05),
]


def crop_box(shot, section, zoom):
    w0, fy, fx = SHOTS[shot]
    w = w0 * (1 - zoom)
    h = w * 16 / 9
    if shot == "TWO":
        cx, cy = 292, 478
    else:
        px, py = PATIENT_FACE if shot == "PAT_M" else FACE[section]
        cy = py - fy * h + h / 2
        cx = (px - fx * w + w / 2) if fx is not None else px + 0.12 * w
    cx = min(max(cx, w / 2), SW - w / 2)
    cy = min(max(cy, h / 2), SH - h / 2)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def ease(x):
    return x * x * (3 - 2 * x)


def finish_frame(img, rng, vign):
    img = img.filter(ImageFilter.UnsharpMask(radius=2.2, percent=55, threshold=2))
    a = np.asarray(img, dtype=np.float32)
    a *= vign
    g = rng.normal(0, 2.6, (H // 2, W // 2)).astype(np.float32)
    a += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    return np.clip(a, 0, 255).astype(np.uint8)


def main():
    os.makedirs(os.path.join(ROOT, "assets/video"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "assets/audio"), exist_ok=True)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.45) / (H / 2)) ** 2)
    vign = (1 - 0.30 * np.clip((r - 0.55) / 0.75, 0, 1) ** 1.6)[..., None].astype(np.float32)
    rng = np.random.default_rng(7)

    out = os.path.join(ROOT, "assets/video/aroll.mp4")
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
         "-pix_fmt", "yuv420p", "-g", "30", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    frames_total = 0
    for first, last, shot, push in PLAN:
        shot_start = SEGS[first]["out_start"]
        shot_end = SEGS[last]["out_start"] + SEGS[last]["src_end"] - SEGS[last]["src_start"]
        for si in range(first, last + 1):
            s = SEGS[si]
            dur = s["src_end"] - s["src_start"]
            n = round(dur * FPS)
            dec = subprocess.run(
                ["ffmpeg", "-v", "error", "-ss", f"{s['src_start']:.3f}", "-i", SRC, "-t", f"{dur + 0.2:.3f}",
                 "-vf", f"{GRADE},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                capture_output=True, check=True).stdout
            fsz = SW * SH * 3
            avail = len(dec) // fsz
            for k in range(n):
                buf = dec[min(k, avail - 1) * fsz:(min(k, avail - 1) + 1) * fsz]
                img = Image.frombuffer("RGB", (SW, SH), buf, "raw", "RGB", 0, 1)
                t = s["out_start"] + k / FPS
                p = ease(min(1, max(0, (t - shot_start) / max(0.01, shot_end - shot_start))))
                box = crop_box(shot, s["section"], push * p)
                img = img.resize((W, H), Image.LANCZOS, box=box)
                enc.stdin.write(finish_frame(img, rng, vign).tobytes())
                frames_total += 1
            print(f"seg {si:2d} {shot:<6} frames {n}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("frames", frames_total, "=", frames_total / FPS, "s")

    # dialogue: same cut points, 8 ms fades at every join
    parts, labels = [], []
    for i, s in enumerate(SEGS):
        d = round(round((s["src_end"] - s["src_start"]) * FPS) / FPS, 4)
        parts.append(f"[0:a]atrim=start={s['src_start']:.3f}:duration={d},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.008,afade=t=out:st={d - 0.008:.4f}:d=0.008[a{i}]")
        labels.append(f"[a{i}]")
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(SEGS)}:v=0:a=1,aresample=48000[out]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[out]",
                    "-ac", "1", "-c:a", "pcm_s24le", os.path.join(ROOT, "assets/audio/dialog-raw.wav")], check=True)


if __name__ == "__main__":
    main()
