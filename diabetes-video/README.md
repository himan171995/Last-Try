# Diabetes Q&A — 16:9 YouTube video (Dr. Mohan Padole)

HyperFrames project for the full-length landscape edit (1920x1080, 30 fps, ~2:31): the whole answer,
tightened, with chapters, the Charaka Samhita shloka, the cover as the title card and an end screen.
`index.html` is generated; edit `build/` and re-run.

```bash
# needs source.mp4 here (gitignored: the repo is public) and assets/cover/{doc_cutout.png,bg_plate.jpg}
# (made by ../diabetes-edit/build/cover.py's asset step; see that file's docstring)
python3 build/edl.py                       # cut list + word timing -> build/edit.json (adds the title-card gap)
python3 -I build/aroll.py source.mp4       # 840x980 panel footage (reframed shots, grade) + cut dialogue
python3 -I ../tools/make_doc_score.py assets/audio/score.wav --seconds 151.1 --lift 8.93 --thin 139.0 --outro 143.1
build/fetch_assets.sh                      # Pixabay-licensed SFX from the vendored skill
python3 build/compose.py                   # graphics, chapters, captions -> index.html, build/sfx.json, build/meta.json
npx hyperframes check
npx hyperframes render --quality delivery --fps 30 --workers 3 --video-frame-format png -o renders/picture.mp4
python3 -I build/mix.py renders/picture.mp4 renders/final.mp4   # voice clean-up, ducked score, SFX, -14 LUFS
python3 build/srt.py captions.srt          # Hinglish CC file + YouTube chapter list
```

| File | Role |
| --- | --- |
| `build/transcript.py` | Kept phrases with source times and Hinglish text; sections in play order. |
| `build/edl.py` | Tightens pauses, frame-snaps cuts, inserts the title-card gap, times words. |
| `build/aroll.py` | Panel footage: per-shot 9:16-ish crops of the source (two-shot, patient, doctor medium/close), grade, Lanczos scale. |
| `build/compose.py` + `build/style.css` | Split layout (panel right, chapter + graphics + captions left) and full-screen scenes: cover title, shloka, anatomy, dairy, rice comparison, kapha chain, sweets, end screen. |
| `build/mix.py` | Dialogue chain, score ducked under the voice, SFX, -14 LUFS master, mux. |
| `build/srt.py` | Caption file for YouTube and the chapter timestamps for the description. |
