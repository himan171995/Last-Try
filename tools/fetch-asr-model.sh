#!/bin/bash
# Downloads the Whisper large-v3-turbo ONNX model (~560 MB) used by tools/transcribe.py.
# Hosted on GitHub releases because HuggingFace is not reachable from cloud sessions.
set -euo pipefail
DEST="${ASR_MODEL_ROOT:-$HOME/.cache/asr}"
NAME="sherpa-onnx-whisper-turbo"
BASE="https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models"
mkdir -p "$DEST"
if [ ! -f "$DEST/$NAME/turbo-encoder.int8.onnx" ]; then
  curl -fsSL "$BASE/$NAME.tar.bz2" | tar xj -C "$DEST"
  rm -f "$DEST/$NAME"/turbo-encoder.onnx "$DEST/$NAME"/turbo-decoder.onnx
fi
[ -f "$DEST/silero_vad.onnx" ] || curl -fsSL -o "$DEST/silero_vad.onnx" "$BASE/silero_vad.onnx"
echo "$DEST/$NAME"
