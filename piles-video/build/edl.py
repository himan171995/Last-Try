"""Cut list and caption timing from transcript.py -> build/edit.json.

Pauses inside a section are tightened to at most GAP_IN; sections butt-join, except where a
section asks for gap_before (picture-only time for the title card). Every segment is a whole
number of frames so picture and sound cut on the same boundary.
"""
import json
import os
import re

from transcript import KEYWORDS, SECTIONS

HERE = os.path.dirname(os.path.abspath(__file__))
PAD_PRE, PAD_POST, GAP_IN, FPS = 0.07, 0.12, 0.22, 30

segments, phrases, words, sections, gaps = [], [], [], [], []
t = 0.0
for name, speaker, gap_before, items in SECTIONS:
    if gap_before:
        g = round(gap_before * FPS) / FPS
        gaps.append({"start": round(t, 3), "end": round(t + g, 3)})
        segments.append({"gap": True, "out_start": round(t, 3), "frames": round(g * FPS), "section": name})
        t += g
    sec_start = t
    prev = None
    for pi, (s, e, text) in enumerate(items):
        a = s - PAD_PRE
        if prev:
            gap = s - prev[1]
            keep = min(gap, GAP_IN + PAD_PRE + PAD_POST)
            a = max(prev[1] + PAD_POST, s - max(0.0, keep - PAD_POST))
            a = min(a, s - 0.03)
            a = max(a, segments[-1]["src_end"])
        b = e + PAD_POST
        if pi + 1 < len(items):
            b = min(b, items[pi + 1][0] - 0.03)
        n = max(1, round((b - a) * FPS))
        b = round(a + n / FPS, 3)
        segments.append({"src_start": round(a, 3), "src_end": b, "frames": n, "out_start": round(t, 3),
                         "section": name, "speaker": speaker})
        ps, pe = t + (s - a), t + (e - a)
        phrases.append({"start": round(ps, 3), "end": round(pe, 3), "text": text, "section": name})
        toks = text.split()
        weights = [max(2, len(re.sub(r"[^\w]", "", w))) + 1.5 for w in toks]
        c = ps
        for w, wt in zip(toks, weights):
            d = (pe - ps) * wt / sum(weights)
            key = re.sub(r"[^\w\-]", "", w.lower())
            words.append({"text": w, "start": round(c, 3), "end": round(c + d, 3), "key": key,
                          "kw": key in KEYWORDS, "section": name})
            c += d
        t += n / FPS
        prev = (s, e)
    sections.append({"name": name, "speaker": speaker, "start": round(sec_start, 3), "end": round(t, 3)})

json.dump({"segments": segments, "phrases": phrases, "words": words, "sections": sections, "gaps": gaps,
           "speech_duration": round(t, 3)}, open(os.path.join(HERE, "edit.json"), "w"), indent=1)
for s in sections:
    print(f"{s['name']:<11} {s['start']:7.2f} - {s['end']:7.2f}  ({s['end'] - s['start']:.2f}s)")
print("programme (speech + title gap)", round(t, 3))
