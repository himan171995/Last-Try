"""Write the Hinglish captions as an .srt for YouTube (CC track) and the chapter list.
Usage: python3 build/srt.py OUT.srt
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(os.path.join(HERE, "edit.json")))
M = json.load(open(os.path.join(HERE, "meta.json")))


def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


lines = []
P = E["phrases"]
for i, p in enumerate(P, 1):
    end = p["end"] + 0.25 if i == len(P) else min(p["end"] + 0.25, P[i]["start"] - 0.02)
    lines.append(f"{i}\n{ts(p['start'])} --> {ts(end)}\n{p['text']}\n")
open(sys.argv[1], "w").write("\n".join(lines))
for c in M["chapters"]:
    t = int(c["t"])
    print(f"{t // 60}:{t % 60:02d} {c['title']}")
