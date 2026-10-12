# Build pipeline

`index.html` and `compositions/*.html` are generated. Edit the generator and re-run it rather than
editing those files by hand (small tweaks in Studio are fine, but re-running the generator
overwrites them).

```bash
# 1. Pre-process the footage (needs source.mp4, which is gitignored):
#    graded 1080p video + cleaned dialogue at -16 LUFS -> assets/video/aroll.mp4
#    (exact ffmpeg command: see "A-roll" below)
# 2. SFX (from the vendored media-use skill) and the music bed (deterministic, royalty-free):
build/fetch_assets.sh
python3 -I ../tools/make_music_bed.py assets/audio/music-bed.wav --seconds 80
ffmpeg -y -i assets/audio/music-bed.wav -af "highpass=f=90,highpass=f=90" -c:a pcm_s16le /tmp/bed.wav && mv /tmp/bed.wav assets/audio/music-bed.wav
# 3. Cut list + caption timings, then the composition:
python3 build/edl.py
python3 build/compose.py
npx hyperframes check
```

| File | Role |
| --- | --- |
| `transcript.py` | Hinglish transcript, one entry per spoken phrase with its source-time span. Fix caption wording here. |
| `voiced.json` | Speech map of the source audio (10 ms energy VAD). Drives pause removal and word timing. |
| `edl.py` | Removes pauses of 0.5 s or more (keeps ~0.27 s of breath), maps source to output time, times every word and groups words into caption pages. Writes `edit.json`. |
| `compose.py` | Writes `index.html` (camera, A-roll cuts, scene hosts, audio) and one sub-composition per scene in `compositions/`. Graphics are anchored to spoken words, so they follow transcript or cut changes automatically. |
| `music-carve.json` | Voiceover carve for the music bed (from `hyperframes-audio/scripts/carve.mjs`). Re-run the carve whenever cuts change. |

## A-roll

```bash
AF="highpass=f=80,afftdn=nf=-25:tn=1,acompressor=threshold=-22dB:ratio=3:attack=8:release=180:makeup=2"
VF="scale=1920:1080:flags=lanczos,colorchannelmixer=rr=0.965:gg=1.03:bb=1.05,eq=contrast=1.05:brightness=0.005:saturation=0.97,curves=master='0/0.02 0.25/0.26 0.5/0.51 0.85/0.86 1/0.98',unsharp=5:5:0.55:5:5:0.0"
# two-pass loudnorm to I=-16 LUFS, TP=-1.5 (measure first, then apply with the measured_* values)
ffmpeg -i source.mp4 -vf "$VF" -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p -g 30 \
  -af "$AF,loudnorm=I=-16:TP=-1.5:LRA=9:<measured values>:linear=true,aresample=48000" \
  -c:a aac -b:a 192k -movflags +faststart assets/video/aroll.mp4
```

The colour grade is baked with ffmpeg because the realtime shader grade needs WebGL, which the
cloud render container does not have. It neutralises about 60% of the warm LED cast measured on
the doctor's white shirt.

## Re-running the carve

```bash
npm i -D @hyperframes/core   # once, in a scratch copy of the project
node ~/.claude/skills/hyperframes-audio/scripts/carve.mjs --comp index.html --bed music-bed
# then copy data-fx-chain / data-fx-carve / data-automation (minus the volume lane) of
# #music-bed into build/music-carve.json and re-run compose.py
```
