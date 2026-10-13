"""Generate an original, royalty-free documentary score (pads, felt piano, heartbeat pulse).

Deterministic (seeded); every sound is synthesised here, so there is nothing to license.
Usage:
  python3 -I tools/make_doc_score.py OUT.wav --seconds 60 --lift 8.93 --thin 53.0 --outro 57.07
"""
import argparse

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000


def mhz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def place(buf, sig, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def piano(m, dur, vel, rng):
    f = mhz(m)
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    B = 0.00025
    for h in range(1, 10):
        fh = f * h * np.sqrt(1 + B * h * h)
        amp = vel / h ** 1.25
        dec = np.exp(-t * (1.1 + 0.55 * h) * (f / 260) ** 0.35)
        out += amp * np.sin(2 * np.pi * fh * t + rng.uniform(0, 6.28)) * dec
    att = np.minimum(1, t / 0.004)
    hammer = rng.normal(0, 1, n) * np.exp(-t * 90) * 0.05 * vel
    rel = np.clip((dur - t) / 0.25, 0, 1)
    return lp((out + lp(hammer, 2500)) * att * rel, 5200)


def pad(ms, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for m in ms:
        for d in (-7, 0, 7):  # cents of detune
            f = mhz(m) * 2 ** (d / 1200)
            ph = rng.uniform(0, 6.28)
            # soft saw: a few harmonics
            for h in range(1, 6):
                out += np.sin(2 * np.pi * f * h * t + ph * h) / (h * 1.6)
    env = np.minimum(1, t / 1.4) * np.clip((dur - t) / 1.6, 0, 1)
    return lp(out * env / (len(ms) * 3), 1800, 4)


def thump(vel):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 52 + 40 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return vel * np.sin(ph) * np.exp(-t * 11) * np.minimum(1, t / 0.003)


def reverb(x, seconds, seed):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-t * 6.9 / seconds)
    ir = lp(ir, 5000)
    ir /= np.sqrt(np.sum(ir ** 2))
    return fftconvolve(x, ir)[: len(x)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--lift", type=float, default=9.0)
    ap.add_argument("--thin", type=float, default=53.0)
    ap.add_argument("--outro", type=float, default=57.0)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    n = int((a.seconds + 0.5) * SR)
    beat = 60 / 80
    bar = 4 * beat

    # D minor: i - VI - III - VII  (Dm, Bb, F, C), voiced around middle C
    prog = [[50, 57, 62, 65], [46, 53, 62, 65], [53, 57, 60, 65], [48, 55, 60, 64]]
    bass = [38, 34, 41, 36]
    pads, keys, low, hb = (np.zeros(n) for _ in range(4))

    # intro: held Dm pad, heartbeat, single high piano notes
    place(pads, pad(prog[0], a.lift + 1.5, rng) * 0.7, 0)
    t = 0.4
    while t < a.lift - 0.4:
        place(hb, thump(0.9), t)
        place(hb, thump(0.55), t + 0.28)
        t += 1.05
    for k, m in enumerate([74, 77, 76, 74, 69, 72]):
        place(keys, piano(m, 2.6, 0.35, rng), 0.8 + k * 1.35)

    # body: progression from the lift to the outro
    t, ci = a.lift, 0
    while t < a.outro:
        ch = prog[ci % 4]
        dur = min(bar, a.outro - t)
        thin = t >= a.thin
        place(pads, pad(ch, dur + 1.6, rng), t)
        place(low, piano(bass[ci % 4], dur + 0.3, 0.55, rng), t)
        arp = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[3] + 12, ch[1] + 24, ch[3] + 12, ch[2] + 12]
        for k, m in enumerate(arp):
            tt = t + k * beat / 2
            if tt >= a.outro - 0.05:
                break
            if thin and k % 2:
                continue
            v = (0.30 if k % 4 == 0 else 0.20) * rng.uniform(0.85, 1.1)
            place(keys, piano(m, 1.8, v, rng), tt)
        if not thin:
            place(hb, thump(0.45), t)
        t += bar
        ci += 1

    # outro: warm resolve on F major add9 with a low D
    end = a.seconds - a.outro
    for k, m in enumerate([41, 53, 60, 65, 67, 69, 72]):
        place(keys, piano(m, end + 0.4, 0.42 if k == 0 else 0.3, rng), a.outro + 0.03 * k)
    place(pads, pad([53, 60, 65, 69], end + 1.0, rng) * 1.2, a.outro - 0.6)

    # air: filtered noise bed
    air = hp(lp(rng.normal(0, 1, n), 7000), 2500) * 0.012

    def norm(x):
        return x / (np.max(np.abs(x)) + 1e-9)

    dry = 0.42 * norm(pads) + 0.5 * norm(keys) + 0.32 * norm(low) + 0.30 * norm(hb)
    L = dry + 0.55 * norm(reverb(dry, 3.2, 1)) * 0.6 + air
    R = dry + 0.55 * norm(reverb(dry, 3.2, 2)) * 0.6 + np.roll(air, 977)
    st = np.stack([hp(L, 35), hp(R, 35)], 1)[: int(a.seconds * SR)]
    fi, fo = int(0.6 * SR), int(1.6 * SR)
    st[:fi] *= np.linspace(0, 1, fi)[:, None]
    st[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    st *= 0.6 / np.max(np.abs(st))
    sf.write(a.out, st.astype(np.float32), SR)


if __name__ == "__main__":
    main()
