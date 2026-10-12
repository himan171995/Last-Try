# Last-Try

Video editing with [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML → MP4), set up for Claude Code.

## Layout

| Path | What it is |
| --- | --- |
| `piles-fissure-edit/` | HyperFrames project for the piles & fissure Q&A video (1920×1080, 30fps, ~74s). Generated from `piles-fissure-edit/build/` (see its README). |
| `.claude/skills/` | HyperFrames agent skills (v0.8.149): router `hyperframes`, `talking-head-recut`, `embedded-captions`, and the domain skills. |
| `.claude/hooks/session-start.sh` | Cloud-session setup: HyperFrames CLI, Chrome Headless Shell, sherpa-onnx. |
| `tools/transcribe.py` | Whisper transcription that handles Hindi (Devanagari) correctly. |
| `tools/fetch-asr-model.sh` | Downloads the Whisper turbo ONNX model (~560 MB) from GitHub releases. |
| `tools/make_music_bed.py` | Generates the royalty-free music bed (tanpura drone, pads, plucks). |

## Workflow

```bash
cd piles-fissure-edit
# put the footage here as source.mp4 (it is gitignored — this repo is public)
npx hyperframes check                               # lint + runtime/layout audit
npx hyperframes preview                             # Studio preview with live reload
npx hyperframes render --quality draft -o renders/draft.mp4
npx hyperframes render --quality delivery -o renders/final.mp4
```

Requirements outside cloud sessions: Node.js 22+, FFmpeg, then `npx hyperframes browser ensure`.
