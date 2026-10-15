"""Transcribe given source spans as whole units (more context than per-phrase ASR).
Usage: python3 -I build/asr_spans.py source.mp4 "a-b" "c-d" ...
"""
import os, subprocess, sys, tempfile
import numpy as np, soundfile as sf, sherpa_onnx as so
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../tools"))
from transcribe import hex_tokens, MODEL_ROOT  # noqa: E402
SR = 16000
with tempfile.NamedTemporaryFile(suffix=".wav") as t:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", sys.argv[1], "-ac", "1", "-ar", str(SR),
                    "-af", "highpass=f=80,afftdn=nf=-25,loudnorm=I=-18:TP=-2", t.name], check=True)
    audio, _ = sf.read(t.name, dtype="float32")
md = os.path.join(MODEL_ROOT, "sherpa-onnx-whisper-turbo")
for lang in ("hi",):
    rec = so.OfflineRecognizer.from_whisper(
        encoder=f"{md}/turbo-encoder.int8.onnx", decoder=f"{md}/turbo-decoder.int8.onnx",
        tokens=hex_tokens(md), language=lang, task="transcribe", num_threads=os.cpu_count() or 4)
    for span in sys.argv[2:]:
        a, b = map(float, span.split("-"))
        seg = audio[int(a * SR): int(b * SR)]
        st = rec.create_stream()
        st.accept_waveform(SR, np.concatenate([seg, np.zeros(max(0, int((29.5 - len(seg) / SR) * SR)), np.float32)]))
        rec.decode_stream(st)
        print(f"[{lang} {span}] " + bytes.fromhex("".join(st.result.tokens)).decode("utf-8", "replace").strip(), flush=True)
