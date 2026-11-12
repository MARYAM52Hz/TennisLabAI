---
name: tennis-serve-reel
description: Turn a tennis serve video plus its CVAT label export into the finished Instagram analysis reel (EN under 30 MiB + FA) with the tennis-reel-kit command line. Use when someone gives a serve clip and CVAT labels and wants the reel.
---
# Tennis serve reel (tennis-reel-kit)

The kit does the whole job: frames and timestamps, label checks, camera, 3D pose and ball, Blender render, overlays, texts, encoding. This skill only runs it correctly and reports honestly.

## Inputs to confirm first
1. The serve video (.MOV/.mp4) and the CVAT export ("CVAT for video 1.1", zip or annotations.xml).
2. View: `back` (camera behind the baseline, court points labelled on frame 0) or `side` (camera beside the player; no court needed). If unsure, look at one frame.
3. The player's real height in metres (`--height`; the scale in the side view, an independent cross-check in the back view; without it 1.80 m is assumed and the reliability grade is capped).
4. Optional: `--charts auto|off|add|replace` (posture-timeline charts; default on for side; back: `add` or `replace`) and `--qc-badge` (print the reliability grade on the sources slide).
4. The Instagram handle if it is not @tennismad.ai.

## Run
1. Find the kit folder (ask where `reel.py` is; if only `tennis-reel-kit.zip` exists, unzip it). Run `python3 reel.py check` (or `./venv/bin/python reel.py check`); if something fails, run `./setup.sh` once or fix the listed item.
2. Start the job in the background so it survives the session, then poll `work/<name>/logs/` every few minutes:
   `setsid nohup python3 reel.py make --view <back|side> --video <video> --labels <cvat> --name <name> [--height H] [--handle @x] > run.log 2>&1 &`
   Expect ~5 min of analysis + 35–60 min of rendering on 2 CPUs. Use `--draft` only for a quick preview, never for the final.
3. If it stops, re-run the identical command (finished work is skipped). On `LABEL PROBLEMS`, give the user the list verbatim, do not guess labels. On `FAILED`, read the log tail it prints; do not patch the code unless asked.
4. Before delivering, check: `logs/calib.log` says "calibration OK" (back view; median court error < 15 px), `job.json` events are plausible (release before contact, bounce after), and look at 2–3 frames of the output (handle visible on every frame, no text covering the player).

## Standards the kit enforces (do not weaken)
Handle on every frame (pill at the top, large on the intro/end cards); text cards long enough to read but with a fast rhythm; translucent cards that never cover the subject; yellow annotations; EN two-pass encode below 30 MiB (SendUserFile limit), FA at CRF 23; back view = posture + ball + height + speed + net clearance, side view = posture/stroke style only (no court-dependent numbers); every number and sentence generated from the measurements.

## Reliability
The `qc` stage writes `qc.json`/`qc.md` (grade A–D, trust level per number, what to fix first). Read it before delivering: A/B publish; C quote only high-trust numbers and tell the user what to relabel; D do not publish. Details: INPUT_STANDARDS_AND_CALIBRATION.md.

## Deliver
Send `output/<name>_reel_EN.mp4` (and the FA file) with SendUserFile and a short note. State plainly: single-camera estimates (angles ±10–15°, speed ±10 %), the back-view result depends on the court labels, reference values are guidance, the flat/kick verdict is a simple rule and may be "unsure". Never claim more accuracy than that.
