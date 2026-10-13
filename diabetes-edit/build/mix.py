"""Final sound mix: cleaned dialogue, generated score ducked under the voice, SFX from build/sfx.json.

Usage: python3 -I build/mix.py PICTURE.mp4 OUT.mp4
Muxes the mix onto the rendered picture (video stream copied) and trims to exactly 60 s.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOTAL = 60.0
PIC, OUT = sys.argv[1], sys.argv[2]
SFX = json.load(open(os.path.join(HERE, "sfx.json")))
A = lambda p: os.path.join(ROOT, p)

VOICE_CHAIN = ("highpass=f=85,lowpass=f=13000,afftdn=nf=-28:tn=1,"
               "equalizer=f=220:t=q:w=1.0:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2.5,"
               "deesser=i=0.25,acompressor=threshold=-21dB:ratio=3:attack=6:release=150:makeup=2")


def loudnorm_params(path, chain, target):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"{chain},loudnorm=I={target}:TP=-2:LRA=8:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    js = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    return (f"loudnorm=I={target}:TP=-2:LRA=8:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
            f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")


def main():
    voice = A("assets/audio/dialog.wav")
    ln = loudnorm_params(A("assets/audio/dialog-raw.wav"), VOICE_CHAIN, -16)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", A("assets/audio/dialog-raw.wav"), "-af",
                    f"{VOICE_CHAIN},{ln},aresample=48000,apad=whole_dur={TOTAL}", "-ac", "2", "-c:a", "pcm_s24le", voice], check=True)

    inputs = ["-i", voice, "-i", A("assets/audio/score.wav")]
    for s in SFX:
        inputs += ["-i", A(s["file"])]
    fc = [
        "[0:a]asplit=2[v][vsc]",
        # score sits ~15 dB under the voice, ducks further while he speaks, and swells for the end card
        "[1:a]volume='0.38*(1+0.9*min(1,max(0,(t-56.8)/0.7)))':eval=frame,aresample=48000[mus]",
        "[mus][vsc]sidechaincompress=threshold=0.035:ratio=5:attack=40:release=450:makeup=1[musd]",
    ]
    labels = []
    for i, s in enumerate(SFX):
        ms = int(round(s["start"] * 1000))
        fc.append(f"[{i + 2}:a]aresample=48000,aformat=channel_layouts=stereo,volume={s['volume'] * 0.55:.3f},adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,highpass=f=60[sfx]")
    fc.append("[v][musd][sfx]amix=inputs=3:normalize=0:dropout_transition=0,"
              f"atrim=0:{TOTAL},alimiter=limit=0.89:attack=3:release=60[pre]")
    pre = A("assets/audio/mix-pre.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[pre]",
                    "-ar", "48000", "-c:a", "pcm_s24le", pre], check=True)
    ln2 = loudnorm_params(pre, "anull", -14)
    mix = A("assets/audio/mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre, "-af", f"{ln2},aresample=48000,atrim=0:{TOTAL}",
                    "-c:a", "pcm_s24le", mix], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", PIC, "-i", mix, "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-t", f"{TOTAL}",
                    "-movflags", "+faststart", OUT], check=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
