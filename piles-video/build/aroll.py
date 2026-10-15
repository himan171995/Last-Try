"""Cut the graded footage and the cleaned dialogue to the edit list (frame-accurate, 30 fps).

Usage: python3 -I build/aroll.py GRADED.mp4 SOURCE.mp4
Writes assets/video/aroll.mp4 (1920x1080, picture only) and assets/audio/dialog.wav.
Dialogue: the young doctor (no mic, 0-9.8 s) and Dr. Padole (lav) get separate chains and are
loudness-matched to -18 LUFS before cutting, so both sit at the same level.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GRADED, SRC = sys.argv[1], sys.argv[2]
FPS, W, H = 30, 1920, 1080
SEGS = json.load(open(os.path.join(HERE, "edit.json")))["segments"]
YOUNG = ("highpass=f=110,afftdn=nf=-30:tn=1,equalizer=f=280:t=q:w=1.2:g=-4,equalizer=f=3200:t=q:w=1.4:g=3.5,"
         "lowpass=f=9500,deesser=i=0.3,acompressor=threshold=-24dB:ratio=3.5:attack=5:release=120:makeup=3")
DOCTOR = ("highpass=f=85,afftdn=nf=-30:tn=1,equalizer=f=220:t=q:w=1.0:g=-1.5,equalizer=f=3000:t=q:w=1.2:g=2,"
          "deesser=i=0.3,acompressor=threshold=-22dB:ratio=3:attack=6:release=150:makeup=2")
TMP = os.path.join(ROOT, "assets/audio")


def loudnorm(inp, chain, out, target=-18):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", inp, "-af", f"{chain},loudnorm=I={target}:TP=-3:LRA=7:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    ln = (f"loudnorm=I={target}:TP=-3:LRA=7:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", inp, "-af", f"{chain},{ln},aresample=48000", "-ac", "1", "-c:a", "pcm_s24le", out], check=True)


def main():
    a, b = os.path.join(TMP, "young.wav"), os.path.join(TMP, "doc.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-t", "9.8", "-vn", "-ac", "1", os.path.join(TMP, "y_raw.wav")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "9.8", "-i", SRC, "-vn", "-ac", "1", os.path.join(TMP, "d_raw.wav")], check=True)
    loudnorm(os.path.join(TMP, "y_raw.wav"), YOUNG, a)
    loudnorm(os.path.join(TMP, "d_raw.wav"), DOCTOR, b)
    clean = os.path.join(TMP, "clean.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-i", b, "-filter_complex", "[0][1]concat=n=2:v=0:a=1", "-c:a", "pcm_s24le", clean], check=True)

    fsz = W * H * 3
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-g", "30", "-movflags", "+faststart",
                            os.path.join(ROOT, "assets/video/aroll.mp4")], stdin=subprocess.PIPE)
    total, parts, labels = 0, [], []
    for i, s in enumerate(SEGS):
        n = s["frames"]
        if s.get("gap"):
            nxt = next(x for x in SEGS[i + 1:] if not x.get("gap"))
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{nxt['src_start']:.3f}", "-i", GRADED, "-frames:v", "1",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
            enc.stdin.write(raw[:fsz] * n)
            parts.append(f"anullsrc=r=48000:cl=mono,atrim=duration={n / FPS:.4f}[a{i}]")
        else:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s['src_start']:.3f}", "-i", GRADED, "-t", f"{n / FPS + 0.2:.3f}",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
            have = len(raw) // fsz
            for k in range(n):
                j = min(k, have - 1)
                enc.stdin.write(raw[j * fsz:(j + 1) * fsz])
            d = n / FPS
            parts.append(f"[0:a]atrim=start={s['src_start']:.3f}:duration={d:.4f},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d=0.01,afade=t=out:st={d - 0.012:.4f}:d=0.012[a{i}]")
        labels.append(f"[a{i}]")
        total += n
    enc.stdin.close()
    enc.wait()
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(SEGS)}:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", clean, "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-ac", "1",
                    "-c:a", "pcm_s24le", os.path.join(TMP, "dialog.wav")], check=True)
    print("frames", total, round(total / FPS, 3))


if __name__ == "__main__":
    main()
