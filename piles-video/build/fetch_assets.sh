#!/bin/bash
# Copies the Pixabay-licensed SFX used by the mix from the vendored media-use skill.
set -euo pipefail
cd "$(dirname "$0")/.."
SRC="../.claude/skills/media-use/audio/assets/sfx"
mkdir -p assets/sfx
for f in $(python3 -c "import json;print(' '.join(sorted({s['file'].split('/')[-1] for s in json.load(open('build/sfx.json'))})))"); do
  cp "$SRC/$f" assets/sfx/
done
cp "$SRC/CREDITS.md" assets/sfx/CREDITS.md
