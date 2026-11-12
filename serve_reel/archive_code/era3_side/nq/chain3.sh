#!/bin/bash
cd /tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad
while ! grep -q ALLDONE nq/render.log; do sleep 10; done
run() { for i in 1 2 3 4 5 6; do python3 -I nq/scene_nr.py $1 0 $2 --samples 4 --plan $3 >> nq/render.log 2>&1; n=$(ls $1/t*.png 2>/dev/null | wc -l); [ "$n" -ge $(( $2 + 1 )) ] && break; done; }
run nq/rf 143 plan_f.json;  PLAN=plan_f.json FADEOUT=0 python3 -I nq/comp.py nq/rf nq/of >> nq/render.log 2>&1
echo ALLDONE2 >> nq/render.log
