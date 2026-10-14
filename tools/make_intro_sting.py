"""Synthesize a short, royalty-free music sting for a channel intro from a JSON cue sheet.

Cue sheet example:
{
  "seconds": 8.0, "key": "D", "seed": 3,
  "drone": {"start": 0.0, "end": 8.0, "level": 0.5},
  "riser": {"start": 0.0, "end": 2.4, "level": 0.35},
  "events": [
    {"type": "bell",   "t": 2.4, "level": 0.8, "note": 0},
    {"type": "impact", "t": 2.4, "level": 0.9},
    {"type": "pluck",  "t": 3.0, "level": 0.5, "note": 7},
    {"type": "shimmer","t": 5.6, "level": 0.4}
  ],
  "tail_fade": 1.2
}
note = semitones above the key's Sa (D3 by default).

Usage: python3 -I tools/make_intro_sting.py CUES.json OUT.wav
"""

import json
import sys

import numpy as np
import soundfile as sf

SR = 48000
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, sig, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def fade_edges(sig, a=0.005, r=0.05):
    n = len(sig)
    ai, ri = int(a * SR), int(r * SR)
    env = np.ones(n)
    env[:ai] = np.linspace(0, 1, ai)
    env[n - ri:] = np.linspace(1, 0, ri)
    return sig * env


def tanpura(f, dur, rng):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for h in range(1, 14):
        amp = 1.0 / h**0.9
        out += amp * np.sin(2 * np.pi * f * h * (1 + rng.uniform(-6e-4, 6e-4)) * t + rng.uniform(0, 6.28)) * np.exp(-t * (0.5 + 0.1 * h)) * (1 - np.exp(-t * (6 + h)))
    return fade_edges(out, 0.01, 0.4)


def drone(root, start, end, rng):
    dur = end - start
    buf = np.zeros(int(dur * SR) + SR)
    t0 = 0.0
    while t0 < dur:
        for k, (m, off) in enumerate([(root - 5, 0.0), (root, 0.6), (root, 1.2), (root - 12, 1.8)]):
            place(buf, tanpura(midi_hz(m), 3.0, rng) * (0.9 if k == 3 else 0.75), t0 + off)
        t0 += 2.4
    t = np.arange(len(buf)) / SR
    pad = sum(np.sin(2 * np.pi * midi_hz(root + s) * t) for s in (0, 7, 12)) / 3
    buf += 0.35 * pad * np.clip(t / 1.5, 0, 1)
    env = np.clip(t / 0.8, 0, 1) * np.clip((dur - t) / 0.8, 0, 1)
    return buf[: int(dur * SR)] * env[: int(dur * SR)]


def riser(dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # sweep a resonant band upward by mixing progressively brighter one-pole filtered noise
    out = np.zeros(n)
    lp = 0.0
    for i in range(n):
        a = 0.995 - 0.25 * (t[i] / dur) ** 2
        lp = a * lp + (1 - a) * noise[i]
        out[i] = noise[i] - lp
    swell = (t / dur) ** 2.2
    tone = np.sin(2 * np.pi * (200 + 900 * (t / dur) ** 2) * t) * 0.25
    return fade_edges((out * 0.6 + tone) * swell, 0.01, 0.02)


def bell(f, rng, dur=4.0):
    t = np.arange(int(dur * SR)) / SR
    partials = [(0.5, 1.0, 0.9), (1.0, 0.9, 1.4), (1.19, 0.55, 2.0), (1.56, 0.45, 2.6), (2.0, 0.35, 3.2), (2.74, 0.25, 4.5), (3.76, 0.15, 6.0)]
    out = np.zeros_like(t)
    for ratio, amp, dec in partials:
        out += amp * np.sin(2 * np.pi * f * ratio * (1 + rng.uniform(-1e-3, 1e-3)) * t) * np.exp(-t * dec / 1.6)
    strike = rng.standard_normal(len(t)) * np.exp(-t * 90) * 0.3
    return fade_edges(out + strike, 0.001, 0.3)


def pluck(f, dur=1.8, bright=0.5):
    # Karplus-Strong string with a sitar-ish buzz
    n = int(dur * SR)
    period = max(2, int(SR / f))
    rng = np.random.default_rng(int(f))
    buf = rng.uniform(-1, 1, period)
    out = np.zeros(n)
    for i in range(n):
        v = buf[i % period]
        out[i] = v
        buf[i % period] = 0.996 * (bright * v + (1 - bright) * buf[(i + 1) % period])
    buzz = np.tanh(out * 2.2) * 0.35
    return fade_edges(out * 0.7 + buzz, 0.002, 0.2)


def impact(rng, dur=2.2):
    t = np.arange(int(dur * SR)) / SR
    f = 55 * np.exp(-t * 3) + 32
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    click = rng.standard_normal(len(t)) * np.exp(-t * 60) * 0.4
    return fade_edges(body + click, 0.001, 0.2)


def shimmer(rng, dur=2.5):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for k in range(18):
        f = rng.uniform(2500, 7000)
        st = rng.uniform(0, dur * 0.5)
        env = np.where(t >= st, np.exp(-(t - st) * rng.uniform(3, 7)), 0)
        out += np.sin(2 * np.pi * f * t) * env * rng.uniform(0.2, 0.5)
    return fade_edges(out / 4, 0.005, 0.3)


def main():
    cues = json.load(open(sys.argv[1]))
    out_path = sys.argv[2]
    rng = np.random.default_rng(cues.get("seed", 3))
    seconds = cues["seconds"]
    root = 50 + NOTE[cues.get("key", "D")] - 2  # Sa at D3 for key D
    mix = np.zeros(int(seconds * SR) + 4 * SR)

    if "drone" in cues:
        d = cues["drone"]
        place(mix, drone(root, d["start"], d["end"], rng) * d.get("level", 0.5), d["start"])
    if "riser" in cues:
        r = cues["riser"]
        place(mix, riser(r["end"] - r["start"], rng) * r.get("level", 0.35), r["start"])
    for ev in cues.get("events", []):
        lvl = ev.get("level", 0.6)
        if ev["type"] == "bell":
            sig = bell(midi_hz(root + 12 + ev.get("note", 0)), rng)
        elif ev["type"] == "pluck":
            sig = pluck(midi_hz(root + 12 + ev.get("note", 0)))
        elif ev["type"] == "impact":
            sig = impact(rng)
        elif ev["type"] == "shimmer":
            sig = shimmer(rng)
        else:
            raise ValueError(ev["type"])
        place(mix, sig * lvl, ev["t"])

    mix = mix[: int(seconds * SR)]
    tf = cues.get("tail_fade", 1.0)
    n = int(tf * SR)
    mix[-n:] *= np.linspace(1, 0, n) ** 1.5
    # gentle stereo spread and soft limiting
    d = int(0.009 * SR)
    st = np.stack([mix, np.concatenate([np.zeros(d), mix[:-d]])], axis=1)
    st = np.tanh(st / (np.max(np.abs(st)) + 1e-9) * 1.4) / np.tanh(1.4) * 0.89
    sf.write(out_path, st.astype(np.float32), SR)


if __name__ == "__main__":
    main()
