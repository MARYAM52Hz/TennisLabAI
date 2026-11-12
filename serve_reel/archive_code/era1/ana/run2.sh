#!/bin/bash
cd /tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad
for s in "$@"; do for t in 1 2 3; do python3 -I ana/build2.py $s >> ana/b2_$1.log 2>&1 && break; done; done
echo ALLDONE >> ana/b2_$1.log
