#!/bin/bash
# Copies the Pixabay-licensed SFX used by the composition from the vendored media-use skill.
set -euo pipefail
cd "$(dirname "$0")/.."
SRC="../.claude/skills/media-use/audio/assets/sfx"
mkdir -p assets/sfx
for f in whoosh whoosh-short pop chime sparkle click-soft ping; do
  cp "$SRC/$f.mp3" assets/sfx/
done
cp "$SRC/CREDITS.md" assets/sfx/CREDITS.md
