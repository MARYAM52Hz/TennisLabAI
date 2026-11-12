# Verification log - building a reel from a fresh clone (2026-11-12)

**Goal:** confirm that someone who only has this repository, a raw phone video and a CVAT label export can produce the reel.

**Procedure**
1. `git clone --depth 1 -b add-serve-reel-kit https://github.com/MARYAM52Hz/TennisLabAI` into an empty directory.
2. `cd serve_reel && python3 reel.py check` -> `ALL GOOD` (python, numpy, scipy, cv2, PIL with libraqm, jax, bpy, ffmpeg/ffprobe, mediapipe pose, assets, fonts).
3. `python3 reel.py make --view side --video IMG_7122.MOV --labels examples/IMG_7122_side_annotations.xml --name fresh_side --height 1.80 --draft`

**Result** (2 CPUs, 8 GB RAM, no GPU)
| stage | time |
|---|---|
| prepare ... qc (analysis) | about 2 min |
| render (Blender, draft samples) | 1483 s |
| build (slides, overlays, composites) | about 8 min |
| encode (two-pass EN, CRF FA) | 179 s |

Outputs: `fresh_side_reel_EN.mp4` 22.7 MiB and `fresh_side_reel_FA.mp4` 8.9 MiB, 88.3 s, 928 x 1696, 30 fps. The `@tennismad.ai` handle is on every sampled frame; posture-timeline slide, scorecard, verdict and sources slides render correctly. Reliability report: grade **A (94/100)** (height given with `--height`).

**Not covered by this run:** `setup.sh` itself (environments were reused: the pose environment `mpenv` was linked from an existing install), the back view beyond the `qc` stage (render of the back view was verified earlier in the stand-alone kit), `--charts add/replace` full renders (the chart slide was rendered and inspected separately for both views), left-handed players, other phones.
