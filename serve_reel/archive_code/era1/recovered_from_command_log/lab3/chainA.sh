#!/bin/bash
cd /tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad
for i in 1 2 3 4; do
  python3 -I lab3/scene_orbit.py lab3/rA 0 209 --samples 4 --plan plan_A.json >> lab3/renderA.log 2>&1
  n=$(ls lab3/rA/t*.png 2>/dev/null | wc -l); [ "$n" -ge 210 ] && break
done
