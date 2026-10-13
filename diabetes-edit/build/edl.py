"""Build the cut list and caption timing from transcript.py.

Within a section, pauses are tightened to at most GAP_IN; sections are joined with GAP_CUT.
Each phrase keeps PAD_PRE / PAD_POST of its source audio so consonants are not clipped.
Word times are spread over the phrase in proportion to word length.
Writes build/edit.json.
"""
import json
import os
import re

from transcript import KEYWORDS, SECTIONS

HERE = os.path.dirname(os.path.abspath(__file__))
PAD_PRE, PAD_POST = 0.07, 0.12
GAP_IN = 0.16
FPS = 30

segments, phrases, words, sections = [], [], [], []
t = 0.0
for si, (name, speaker, items) in enumerate(SECTIONS):
    sec_start = t
    for pi, (s, e, text) in enumerate(items):
        a = s - PAD_PRE
        if pi > 0:
            prev_e = items[pi - 1][1]
            gap = s - prev_e
            # keep up to GAP_IN of the real pause, split across the two pads
            keep = min(gap, GAP_IN + PAD_PRE + PAD_POST)
            a = max(prev_e + PAD_POST, s - max(0.0, keep - PAD_POST))
            a = min(a, s - 0.03)
        if pi > 0 and segments and segments[-1]["section"] == name:
            a = max(a, segments[-1]["src_end"])  # never replay audio already used
        b = e + PAD_POST
        if pi + 1 < len(items):
            b = min(b, items[pi + 1][0] - 0.03)
        # whole frames at 30 fps, so picture and sound cut on the same boundary
        dur = max(1, round((b - a) * FPS)) / FPS
        b = round(a + dur, 3)
        segments.append({"src_start": round(a, 3), "src_end": round(b, 3), "out_start": round(t, 3),
                         "section": name, "speaker": speaker})
        ps, pe = t + (s - a), t + (e - a)
        phrases.append({"start": round(ps, 3), "end": round(pe, 3), "text": text, "section": name})
        toks = text.split()
        weights = [max(2, len(re.sub(r"[^\w]", "", w))) + 1.5 for w in toks]
        tot = sum(weights)
        c = ps
        for w, wt in zip(toks, weights):
            d = (pe - ps) * wt / tot
            key = re.sub(r"[^\w\-]", "", w.lower())
            words.append({"text": w, "start": round(c, 3), "end": round(c + d, 3),
                          "key": key, "kw": key in KEYWORDS, "section": name})
            c += d
        t += dur
    sections.append({"name": name, "speaker": speaker, "start": round(sec_start, 3), "end": round(t, 3)})
speech = round(t, 3)

json.dump({"segments": segments, "phrases": phrases, "words": words, "sections": sections,
           "speech_duration": speech}, open(os.path.join(HERE, "edit.json"), "w"), indent=1)
for s in sections:
    print(f"{s['name']:<11} {s['start']:6.2f} - {s['end']:6.2f}  ({s['end'] - s['start']:.2f}s)")
print("speech duration", speech)
