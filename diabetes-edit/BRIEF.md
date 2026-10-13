---
workflow: general-video
flow: automation
storyboard: no
message: "Dr. Mohan Padole explains, from Charaka Samhita, why diabetes is rising: stress, excess dairy, new grain (kapha), frequent sweets; comfort plus stress."
destination: youtube-shorts
aspect: 1080x1920
language: hi-Latn
audience: general Hindi-speaking public; prospective patients of the hospital
length: exactly 60s (cut from a 3:29 source)
angle: doctor Q&A, premium medical documentary
---

## Intent

Edit an existing two-person consultation recording: a young man in a white coat asks
why 6 to 8 of every 10 patients are diabetic; Dr. Mohan Padole answers from Charaka Samhita.
Cut to exactly 60 s, keep the doctor's face, voice and words, add no claims or dialogue.

## Assets

- source.mp4: WhatsApp video, 576x1024 (rotated 1024x576 stream), 24 fps, 3:29. Local only:
  the repo is public, so footage and anything derived from it is gitignored.

## Customizations (user-confirmed)

- Length: exactly 60 s (never above 120 s).
- Captions: Hinglish (Roman script), word highlight, keywords in teal.
- Lower third: Dr. Mohan Padole, Saikrupa Ayurvedic Hospital, Nagpur.
- B-roll and animated anatomy (pancreas, insulin, glucose), motion graphics, transitions,
  colour grade, SFX, music. No medical disclaimer card.
- Export 1080x1920 MP4.

## Notes

- Stock sites (Pexels, Pixabay, Wikimedia, YouTube Audio Library) are unreachable from this
  environment, so B-roll is illustrated (Fluent 3D emoji, MIT, plus hand-built SVG anatomy),
  SFX are the Pixabay-licensed set bundled with the media-use skill, and the score is
  synthesised by tools/make_doc_score.py (original, nothing to license).
- On-screen text only restates what is said, or labels anatomy (Pancreas, Insulin, Glucose).
