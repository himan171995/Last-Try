# Last-Try

Video editing with [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML → MP4), set up for Claude Code.

## Layout

| Path | What it is |
| --- | --- |
| `diabetes-video/` | HyperFrames project for the full 16:9 YouTube video of the same talk (1920×1080, 30 fps, ~2:31) with chapters, shloka, cover title card and end screen. |
| `diabetes-edit/` | HyperFrames project for the diabetes Q&A short with Dr. Mohan Padole (1080×1920, 30 fps, 60 s). Generated from `diabetes-edit/build/` (see its README). |
| `.claude/skills/` | HyperFrames agent skills (v0.8.149): router `hyperframes`, `talking-head-recut`, `embedded-captions`, and the domain skills. |
| `.claude/hooks/session-start.sh` | Cloud-session setup: HyperFrames CLI, Chrome Headless Shell, sherpa-onnx. |
| `tools/transcribe.py` | Whisper transcription that handles Hindi (Devanagari) correctly. |
| `tools/fetch-asr-model.sh` | Downloads the Whisper turbo ONNX model (~560 MB) from GitHub releases. |
| `tools/make_music_bed.py` | Generates a royalty-free tanpura/pad music bed. |
| `tools/make_doc_score.py` | Generates the royalty-free documentary score (pads, felt piano, heartbeat pulse). |

Source footage and renders are gitignored (this repo is public).
