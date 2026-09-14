#!/bin/zsh
set -euo pipefail
destination="${1:-work/synthetic-benchmark.mp4}"
mkdir -p "$(dirname "$destination")"
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "testsrc2=size=1280x720:rate=30:duration=3" \
  -f lavfi -i "color=c=0x101820:size=1280x720:rate=30:duration=1" \
  -f lavfi -i "smptebars=size=1280x720:rate=30:duration=3" \
  -f lavfi -i "mandelbrot=size=1280x720:rate=30:maxiter=80" \
  -filter_complex "[3:v]trim=duration=3,setpts=PTS-STARTPTS[m];[0:v][1:v][2:v][m]concat=n=4:v=1:a=0,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -preset fast "$destination"
print -r -- "$destination"

