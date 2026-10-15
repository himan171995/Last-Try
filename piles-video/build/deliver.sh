#!/bin/bash
# Verify the master and make the chat-deliverable copy (<= ~29 MB) plus a 2-second frame sheet.
set -euo pipefail
cd "$(dirname "$0")/.."
M=renders/final_master.mp4
OUT=output/piles_dr_padole_final.mp4
TMPD=${TMPDIR:-/tmp}/piles_deliver; mkdir -p "$TMPD"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate,nb_frames,sample_rate -of compact "$M"
ffmpeg -v error -y -i "$M" -map 0:v:0 -c:v libx264 -preset slow -b:v 3500k -maxrate 6000k -bufsize 8000k -pix_fmt yuv420p -profile:v high -g 60 -pass 1 -passlogfile "$TMPD/p" -an -f mp4 /dev/null
ffmpeg -v error -y -i "$M" -map 0:v:0 -map 0:a:0 -c:v libx264 -preset slow -b:v 3500k -maxrate 6000k -bufsize 8000k -pix_fmt yuv420p -profile:v high -g 60 -pass 2 -passlogfile "$TMPD/p" -c:a aac -b:a 192k -ar 48000 -movflags +faststart -t 60 "$OUT"
ffprobe -v error -show_entries format=duration,size:stream=nb_frames -of compact "$OUT"
ffmpeg -hide_banner -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -A14 Summary | grep -E "I:|Peak"
ffmpeg -v error -y -i "$OUT" -vf "fps=1/2,scale=384:216,tile=6x5" -frames:v 1 "$TMPD/sheet.jpg"
echo "$TMPD/sheet.jpg"
