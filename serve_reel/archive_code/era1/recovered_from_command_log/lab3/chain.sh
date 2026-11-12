#!/bin/bash
cd /tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad
for i in 1 2 3 4 5 6; do
  python3 -I lab3/scene_orbit.py lab3/r 0 569 --samples 4 >> lab3/render.log 2>&1
  n=$(ls lab3/r/t*.png 2>/dev/null | wc -l); [ "$n" -ge 570 ] && break
done
