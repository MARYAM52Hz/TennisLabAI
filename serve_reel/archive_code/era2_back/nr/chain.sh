#!/bin/bash
cd /tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad
run() { # outdir last plan
  for i in 1 2 3 4 5 6; do
    python3 -I nr/scene_nr.py $1 0 $2 --samples 4 --plan $3 >> nr/render.log 2>&1
    n=$(ls $1/t*.png 2>/dev/null | wc -l); [ "$n" -ge $(( $2 + 1 )) ] && break
  done
}
run nr/ro 149 plan_o.json;  PLAN=plan_o.json FADEOUT=0 python3 -I nr/comp.py nr/ro nr/oo >> nr/render.log 2>&1
run nr/rf 143 plan_f.json;  PLAN=plan_f.json FADEOUT=0 python3 -I nr/comp.py nr/rf nr/of >> nr/render.log 2>&1
run nr/rl 239 plan_l.json;  PLAN=plan_l.json FADEOUT=1 python3 -I nr/comp.py nr/rl nr/ol >> nr/render.log 2>&1
echo ALLDONE >> nr/render.log
