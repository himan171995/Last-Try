"""Split the source audio into short spoken phrases (energy VAD) and transcribe each one.

Usage: python3 -I build/phrases.py source.mp4 out.json
Writes [{start, end, text}] with phrase-level source times (10 ms resolution).
"""
import json, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf, sherpa_onnx as so
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../tools"))
from transcribe import hex_tokens, MODEL_ROOT  # noqa: E402

SR = 16000
src, out = sys.argv[1], sys.argv[2]
with tempfile.NamedTemporaryFile(suffix=".wav") as t:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", str(SR),
                    "-af", "highpass=f=80,afftdn=nf=-25,loudnorm=I=-18:TP=-2", t.name], check=True)
    audio, _ = sf.read(t.name, dtype="float32")

hop = SR // 100
rms = np.sqrt(np.convolve(audio ** 2, np.ones(hop * 3) / (hop * 3), "same")[::hop])
db = 20 * np.log10(rms + 1e-9)
thr = np.percentile(db, 30) + 0.45 * (np.percentile(db, 95) - np.percentile(db, 30))
v = db > thr
# close gaps < 0.25 s, drop blips < 0.12 s
segs, i, n = [], 0, len(v)
while i < n:
    if v[i]:
        j = i
        while j < n and v[j]:
            j += 1
        segs.append([i, j]); i = j
    else:
        i += 1
merged = []
for s in segs:
    if merged and s[0] - merged[-1][1] < 25:
        merged[-1][1] = s[1]
    else:
        merged.append(s)
merged = [s for s in merged if s[1] - s[0] >= 12]
json.dump([[a / 100, b / 100] for a, b in merged], open(out.replace(".json", "-voiced.json"), "w"))

md = os.path.join(MODEL_ROOT, "sherpa-onnx-whisper-turbo")
rec = so.OfflineRecognizer.from_whisper(
    encoder=f"{md}/turbo-encoder.int8.onnx", decoder=f"{md}/turbo-decoder.int8.onnx",
    tokens=hex_tokens(md), language="hi", task="transcribe", num_threads=os.cpu_count() or 4)
res = []
for a, b in merged:
    s, e = a / 100, b / 100
    seg = audio[max(0, int((s - 0.1) * SR)): int((e + 0.1) * SR)]
    st = rec.create_stream()
    st.accept_waveform(SR, np.concatenate([seg, np.zeros(int((29.5 - len(seg) / SR) * SR), np.float32)]))
    rec.decode_stream(st)
    txt = bytes.fromhex("".join(st.result.tokens)).decode("utf-8", "replace").strip()
    print(f"[{s:7.2f} - {e:7.2f}] {txt}", flush=True)
    res.append({"start": s, "end": e, "text": txt})
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
