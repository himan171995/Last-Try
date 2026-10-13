#!/bin/bash
# Prepares a Claude Code cloud session for HyperFrames video editing.
# Idempotent: every step is skipped when its result is already present.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

HF_VERSION="0.8.149"

# HyperFrames CLI (cached in the npx store) + the Chrome Headless Shell it renders with.
npx -y "hyperframes@${HF_VERSION}" browser ensure >/dev/null

# Local speech-to-text runtime used by tools/transcribe.py (model is fetched on demand).
python3 -c "import sherpa_onnx, soundfile" 2>/dev/null \
  || pip install -q sherpa-onnx soundfile >/dev/null 2>&1

echo "HyperFrames ${HF_VERSION} ready (CLI, Chrome Headless Shell, sherpa-onnx)."
