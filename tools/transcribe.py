"""Transcribe a video/audio file with Whisper (sherpa-onnx), including Hindi.

Works around two sherpa-onnx issues that garble non-Latin scripts:
  * tokens are decoded one at a time, so multi-byte UTF-8 (Devanagari) is lost.
    We swap in a token table that emits each token's bytes as hex, then decode.
  * output length is capped per second of audio, truncating byte-heavy scripts.
    Each speech chunk is padded with silence to lift the cap.

Usage:
  tools/fetch-asr-model.sh
  python3 -I tools/transcribe.py INPUT OUT.json [--lang hi] [--task transcribe]
"""

import argparse
import base64
import json
import os
import subprocess
import tempfile

import numpy as np
import sherpa_onnx as so
import soundfile as sf

SR = 16000
MODEL_ROOT = os.environ.get("ASR_MODEL_ROOT", os.path.expanduser("~/.cache/asr"))


def hex_tokens(model_dir):
    out = os.path.join(model_dir, "hex-tokens.txt")
    if not os.path.exists(out):
        lines = []
        with open(os.path.join(model_dir, "turbo-tokens.txt"), encoding="utf-8") as f:
            for line in f:
                tok, idx = line.rstrip("\n").rsplit(" ", 1)
                hexed = base64.b64decode(tok).hex().encode()
                lines.append(f"{base64.b64encode(hexed).decode()} {idx}")
        with open(out, "w") as f:
            f.write("\n".join(lines) + "\n")
    return out


def load_audio(path):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(SR),
             "-af", "highpass=f=80,afftdn=nf=-25,loudnorm=I=-18:TP=-2", tmp.name],
            check=True,
        )
        audio, _ = sf.read(tmp.name, dtype="float32")
    return audio


def speech_chunks(audio, vad_model, max_len=10.0, join_gap=0.8):
    cfg = so.VadModelConfig()
    cfg.silero_vad.model = vad_model
    cfg.silero_vad.min_silence_duration = 0.5
    cfg.silero_vad.min_speech_duration = 0.25
    cfg.silero_vad.max_speech_duration = 20
    cfg.sample_rate = SR
    vad = so.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
    segs = []

    def drain():
        while not vad.empty():
            segs.append((vad.front.start / SR, len(vad.front.samples) / SR))
            vad.pop()

    win = cfg.silero_vad.window_size
    for i in range(0, len(audio), win):
        vad.accept_waveform(audio[i : i + win])
        drain()
    vad.flush()
    drain()

    chunks = []
    for start, dur in segs:
        if chunks and start - chunks[-1][1] < join_gap and start + dur - chunks[-1][0] < max_len:
            chunks[-1][1] = start + dur
        else:
            chunks.append([start, start + dur])
    return chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--lang", default="hi")
    ap.add_argument("--task", default="transcribe")
    ap.add_argument("--model-dir", default=os.path.join(MODEL_ROOT, "sherpa-onnx-whisper-turbo"))
    args = ap.parse_args()

    rec = so.OfflineRecognizer.from_whisper(
        encoder=os.path.join(args.model_dir, "turbo-encoder.int8.onnx"),
        decoder=os.path.join(args.model_dir, "turbo-decoder.int8.onnx"),
        tokens=hex_tokens(args.model_dir),
        language=args.lang,
        task=args.task,
        num_threads=os.cpu_count() or 4,
    )
    audio = load_audio(args.input)
    result = []
    for start, end in speech_chunks(audio, os.path.join(MODEL_ROOT, "silero_vad.onnx")):
        seg = audio[max(0, int((start - 0.15) * SR)) : int((end + 0.15) * SR)]
        pad = np.zeros(max(0, int((29.9 - len(seg) / SR) * SR)), dtype=np.float32)
        stream = rec.create_stream()
        stream.accept_waveform(SR, np.concatenate([seg, pad]))
        rec.decode_stream(stream)
        text = bytes.fromhex("".join(stream.result.tokens)).decode("utf-8", "replace").strip()
        print(f"[{start:7.2f} - {end:7.2f}] {text}", flush=True)
        result.append({"start": round(start, 2), "end": round(end, 2), "text": text})

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
