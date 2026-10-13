"""Generate a calm, royalty-free music bed: tanpura-style drone, soft pads, sparse plucks.

Deterministic (seeded). Usage:
  python3 -I tools/make_music_bed.py OUT.wav --seconds 80 --key D
"""

import argparse

import numpy as np
import soundfile as sf

SR = 48000
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(semitones_from_a4):
    return 440.0 * 2 ** (semitones_from_a4 / 12)


def midi_hz(m):
    return hz(m - 69)


def env_adsr(n, a, d, s, r):
    t = np.arange(n) / SR
    total = n / SR
    e = np.where(t < a, t / max(a, 1e-4), 1.0)
    e = np.where((t >= a) & (t < a + d), 1 - (1 - s) * (t - a) / max(d, 1e-4), e)
    e = np.where(t >= a + d, s, e)
    e = np.where(t > total - r, e * np.clip((total - t) / max(r, 1e-4), 0, 1), e)
    return e


def tanpura_pluck(f, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for h in range(1, 14):
        amp = (1.0 / h**0.9) * (1.15 if h in (3, 5) else 1.0)
        det = 1 + rng.uniform(-0.0006, 0.0006)
        decay = np.exp(-t * (0.55 + 0.11 * h))
        # jawari: harmonics bloom slightly after the attack
        bloom = 1 - np.exp(-t * (6 + h))
        out += amp * np.sin(2 * np.pi * f * h * det * t + rng.uniform(0, 6.28)) * decay * bloom
    return out * env_adsr(n, 0.01, 0.0, 1.0, 0.4)


def pad(freqs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for d in (-0.12, 0.0, 0.12):
            ff = f * 2 ** (d / 12 / 4)
            out += np.sin(2 * np.pi * ff * t) + 0.18 * np.sin(2 * np.pi * 2 * ff * t)
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.09 * t)
    return out / (3 * len(freqs)) * env_adsr(n, 2.2, 0.5, 0.9, 2.4) * lfo


def pluck(f, dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = sum((0.6**k) * np.sin(2 * np.pi * f * (k + 1) * t) for k in range(5))
    return out * np.exp(-t * 3.2) * env_adsr(n, 0.004, 0.0, 1.0, 0.2)


def place(buf, sig, start):
    i = int(start * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[: j - i]


def lowpass(x, cutoff):
    # one-pole low-pass, applied twice for 12 dB/oct
    a = np.exp(-2 * np.pi * cutoff / SR)
    for _ in range(2):
        y = np.empty_like(x)
        acc = 0.0
        for i, v in enumerate(x):
            acc = (1 - a) * v + a * acc
            y[i] = acc
        x = y
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=80)
    ap.add_argument("--key", default="D")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    n = int(args.seconds * SR)
    root = 48 + NOTE[args.key]  # Sa around D3

    drone = np.zeros(n)
    cycle = 4.2
    t0 = 0.0
    while t0 < args.seconds:
        for k, (m, off) in enumerate([(root - 5, 0.0), (root, 1.05), (root, 2.1), (root - 12, 3.15)]):
            place(drone, tanpura_pluck(midi_hz(m), cycle + 2.0, rng) * (0.8 if k else 0.9), t0 + off)
        t0 += cycle

    # I - IV - V - vi colours over the drone, 8.4 s per chord
    chords = [[0, 4, 7], [5, 9, 12], [7, 11, 14], [-3, 0, 4]]
    pads = np.zeros(n)
    t0, ci = 0.0, 0
    while t0 < args.seconds:
        freqs = [midi_hz(root + 12 + s) for s in chords[ci % 4]]
        place(pads, pad(freqs, 9.6), t0)
        t0 += 8.4
        ci += 1

    # sparse pentatonic plucks (santoor-like), with a soft echo
    scale = [0, 2, 4, 7, 9, 12, 14, 16]
    plucks = np.zeros(n)
    t = 2.1
    while t < args.seconds - 3:
        if rng.random() < 0.55:
            m = root + 24 + scale[rng.integers(0, len(scale))]
            p = pluck(midi_hz(m)) * rng.uniform(0.5, 0.8)
            place(plucks, p, t)
            place(plucks, p * 0.35, t + 0.35)
            place(plucks, p * 0.15, t + 0.70)
        t += 0.7 * rng.integers(1, 4)

    mix = 0.55 * drone / np.max(np.abs(drone)) + 0.35 * pads / np.max(np.abs(pads)) + 0.22 * plucks / np.max(np.abs(plucks))
    mix = lowpass(mix, 6500)
    fade = np.ones(n)
    fi, fo = int(2.5 * SR), int(4.0 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    mix *= fade
    # gentle stereo: delay one side by a few ms
    d = int(0.011 * SR)
    left = mix
    right = np.concatenate([np.zeros(d), mix[:-d]])
    st = np.stack([left, right], axis=1)
    st *= 0.5 / np.max(np.abs(st))
    sf.write(args.out, st.astype(np.float32), SR)


if __name__ == "__main__":
    main()
