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

---

# Follow-up tests (2026-11-12 / 13): the items that were not covered above

All runs used the same fresh clone, plus the fixes described below.

## 1. `setup.sh` from scratch
`bash setup.sh` was run in the clone: it creates `venv/` (Blender-as-a-module, jax, scipy, opencv, pillow) and `mpenv/` (Python 3.12 + mediapipe 0.10.14 for pose), then runs `reel.py check`, which printed `ALL GOOD` (python, numpy, scipy, cv2, PIL with libraqm, jax, bpy, ffmpeg/ffprobe, mediapipe pose, assets, fonts).

## 2. Back view, full render from the fresh clone
`reel.py make --view back --video IMG_7125.MOV --labels examples/IMG_7125_back_annotations.xml --name b_add --height 1.80 --charts add --qc-badge --draft` (render -> build -> encode):
EN 25.6 MiB, FA 14.4 MiB, 106.6 s, handle on every sampled frame, "Reliability: A 87 / 100" badge on the sources slide, posture timeline and long shot both present.

## 3. `--charts` modes (full renders)
| view | mode | job charts | result |
|---|---|---|---|
| back | `add` | both | long shot + posture timeline, 106.6 s, EN 25.6 MiB |
| back | `replace` | timeline | no long shot, posture timeline only, 95.6 s, EN 23.6 MiB, FA 10.4 MiB |
| side | `off` | none | see section 6 |
Changing `--charts` after a build shifts the segment indices: delete `nr|nq/fin_en` and `fin_fa` before re-running `--from build`.

## 4. Left-handed players (mirrored inputs)
The video was flipped horizontally and the CVAT labels were mirrored accordingly (`tools/make_variant_inputs.py mirror`, left/right names swapped). `--hand auto` compares each wrist with the racket handle at contact; the left wrist is closer, so the pipeline mirrors the video and labels back to a right-handed canonical form and records `hand_detected: left`, `mirrored: true`.

| input | grade | contact height | front/back knee/trunk trust |
|---|---|---|---|
| side original | A 94.3 | 2.77 m (1.54 x height) | high / high / high |
| side mirrored | A 94.3 | 2.77 m | identical |
| back original | A 87.4 | - | high / high / high (trunk 82), speed medium |
| back mirrored | A 87.5 | - | identical |


## 5. Other phones: resolution, orientation, focal length
Variants made with `tools/make_variant_inputs.py`: 1.5x upscale (1080 x 1920) and a clockwise-rotated copy stored with a display-rotation tag (as phones do).
* All inputs are normalised to a working resolution of 1280 px on the long side; the original size is kept as `W_src/H_src` and `scale_to_working`.
* Side view: 1.5x and rotation-tag variants reproduce the original (grade A 94.3, contact height 2.77 m, same trust levels).
* Back view, 1.5x: grade A 87.4, same calibration (f = 657 px = 0.513 x image height) and the same metrics.
* Bugs found and fixed: (a) the side-view motion detector read the source video with the scaled size, giving garbage (contact height -50 m, grade B); it now uses `W_src/H_src`. (b) An implausible contact height was not a critical failure; `C_contact_h` is now critical outside 1.05-2.05 x the 1.55 reference. (c) The first rotation variant was built with the wrong transpose, so the test input was wrong, not the pipeline.
* New safeguards: the side-view focal prior is `0.515 x max(W, H)`; landscape footage triggers a warning and the `V_orient` QC check (score 50).
* **Still untested:** real footage from other phones/lenses (ultra-wide, telephoto, 0.5x), landscape footage and portrait video that is not 9:16. The focal length of the back view is fitted from the court lines, so it adapts; the side view relies on the prior, so a different lens needs `--height` plus a check of the C_focal line in `qc.md`.
