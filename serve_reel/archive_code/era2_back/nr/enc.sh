#!/bin/bash
cd /tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad
F="-framerate 30 -i nr/fin_en/f%05d.png -vf format=yuv420p -c:v libx264 -preset slow -b:v 2350k -maxrate 4500k -bufsize 6000k -pix_fmt yuv420p -movflags +faststart"
ffmpeg -y -loglevel error $F -pass 1 -passlogfile nr/pl -an -f mp4 /dev/null
ffmpeg -y -loglevel error $F -pass 2 -passlogfile nr/pl out/IMG7125_serve_analysis_EN.mp4
ffmpeg -y -loglevel error -framerate 30 -i nr/fin_fa/f%05d.png -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p -movflags +faststart out/IMG7125_serve_analysis_FA.mp4
echo ENCDONE > nr/enc.done
