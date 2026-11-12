#!/bin/bash
cd /tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad
while pgrep -f "scene_match.py mt_full 46" >/dev/null; do sleep 5; done
python3 -I pipeline/scene_match.py mt_full 1 45 --pct 100 --samples 6 --key 1000 > mt_full/log_1.txt 2>&1
