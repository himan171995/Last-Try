"""Edit decision list: pause removal, source->output time map, word and caption timings.

Writes build/edit.json, consumed by build/compose.py.
"""

import json
import os
import re

from transcript import KEYWORDS, SENTENCES

HERE = os.path.dirname(os.path.abspath(__file__))

LEAD = 0.12  # audio kept before a voiced segment
TAIL = 0.16  # audio kept after a voiced segment
MIN_CUT_GAP = 0.5  # only pauses at least this long are cut
SHOT_CHANGE = 6.267  # interviewer solo shot -> two-shot
FIRST_IN = 0.0
LAST_OUT = 90.45

PAGE_MAX_CHARS = 30
PAGE_MAX_WORDS = 5


def load_voiced():
    with open(os.path.join(HERE, "voiced.json")) as f:
        voiced = json.load(f)["voiced"]
    # drop the click at the shot change
    return [v for v in voiced if not (SHOT_CHANGE - 0.1 <= v[0] <= SHOT_CHANGE + 0.3 and v[1] - v[0] < 0.3)]


def keep_ranges(voiced):
    ranges = []
    for v0, v1 in voiced:
        a, b = max(FIRST_IN, v0 - LEAD), min(LAST_OUT, v1 + TAIL)
        if ranges and v0 - prev_end < MIN_CUT_GAP:
            ranges[-1][1] = b
        else:
            ranges.append([a, b])
        prev_end = v1
    ranges[0][0] = FIRST_IN
    ranges[-1][1] = LAST_OUT
    return ranges


def build_segments(ranges):
    segs, t = [], 0.0
    for a, b in ranges:
        segs.append({"src_in": round(a, 3), "src_out": round(b, 3), "out_start": round(t, 3)})
        t += b - a
    return segs, round(t, 3)


def src_to_out(segs, ts):
    for s in segs:
        if ts < s["src_in"]:
            return s["out_start"]
        if ts <= s["src_out"]:
            return s["out_start"] + ts - s["src_in"]
    last = segs[-1]
    return last["out_start"] + last["src_out"] - last["src_in"]


def syllables(word):
    core = re.sub(r"[^a-z]", "", word.lower())
    return max(1, len(re.findall(r"[aeiouy]+", core)))


def word_times(voiced, s0, s1, words):
    spans = [(max(a, s0), min(b, s1)) for a, b in voiced if b > s0 and a < s1]
    spans = [s for s in spans if s[1] - s[0] > 0.02] or [(s0, s1)]
    total = sum(b - a for a, b in spans)
    weights = [syllables(w) for w in words]
    wsum = float(sum(weights))

    def at(frac):
        need = frac * total
        for a, b in spans:
            if need <= b - a:
                return a + need
            need -= b - a
        return spans[-1][1]

    out, acc = [], 0.0
    for w, wt in zip(words, weights):
        start = at(acc / wsum)
        acc += wt
        end = at(acc / wsum)
        out.append((start, end))
    return out


def is_keyword(word):
    return re.sub(r"[^a-z\-]", "", word.lower()) in KEYWORDS


def build_words(voiced, segs):
    words = []
    for idx, (s0, s1, text) in enumerate(SENTENCES):
        toks = text.split()
        for tok, (a, b) in zip(toks, word_times(voiced, s0, s1, toks)):
            words.append({
                "text": tok,
                "sentence": idx,
                "src": [round(a, 3), round(b, 3)],
                "start": round(src_to_out(segs, a), 3),
                "end": round(src_to_out(segs, b), 3),
                "key": is_keyword(tok),
            })
    return words


def balanced_chunks(ws):
    total = len(" ".join(w["text"] for w in ws))
    k = max(1, -(-total // PAGE_MAX_CHARS), -(-len(ws) // PAGE_MAX_WORDS))
    if k == 1:
        return [ws]
    target = total / k
    chunks, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        left = len(ws) - i - 1
        if len(chunks) < k - 1 and len(" ".join(x["text"] for x in cur)) >= target * 0.92 and left >= 2:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def build_pages(words):
    clauses, cur = [], []
    for w in words:
        if cur and (w["sentence"] != cur[-1]["sentence"] or (cur[-1]["text"][-1] == "," and len(cur) >= 2)):
            clauses.append(cur)
            cur = []
        cur.append(w)
    clauses.append(cur)
    pages = [c for clause in clauses for c in balanced_chunks(clause)]
    out = []
    for i, p in enumerate(pages):
        start = p[0]["start"] - 0.06
        end = p[-1]["end"] + 0.3
        if i + 1 < len(pages):
            nxt = pages[i + 1][0]["start"] - 0.06
            end = nxt if nxt - p[-1]["end"] < 0.7 else min(end, nxt)
        out.append({"start": round(max(0, start), 3), "end": round(end, 3), "words": p})
    return out


def main():
    voiced = load_voiced()
    segs, total = build_segments(keep_ranges(voiced))
    words = build_words(voiced, segs)
    pages = build_pages(words)
    data = {"segments": segs, "speech_duration": total, "words": words, "pages": pages}
    with open(os.path.join(HERE, "edit.json"), "w") as f:
        json.dump(data, f, indent=1)
    print(f"{len(segs)} segments, speech timeline {total:.2f}s (source 92.77s), {len(pages)} caption pages")


if __name__ == "__main__":
    main()
