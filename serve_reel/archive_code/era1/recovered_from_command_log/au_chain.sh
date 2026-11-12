#!/bin/bash
cd /tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad
while kill -0 1871 2>/dev/null; do sleep 5; done
python3 -I auto/scene_auto.py au_full 182 222 --pct 75 --samples 4 > au_full/log_182b.txt 2>&1
