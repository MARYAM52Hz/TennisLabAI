# Pipeline in detail (kit stage names in `code`)

Conventions used everywhere: **world** x along the net, y away from the camera (back view) / toward the net (side view: x toward the camera), z up, metres. Baseline y = −11.885, singles half-width 4.115, doubles 5.485, service line 6.40. Image px: 720×1280 source, reel canvas **928×1696**. Frame files: `f0001` = frame 0 (**off-by-one trap**: use `f{S+1}`). Scripts find their root through env `REEL_JOB` (kit) or the hard-coded `SP=` path (old flat code, see RESTORE.md). Run Python with `-I` (isolated) — scripts do their own `sys.path` handling.

## Stage map (`reel.py make`, resumable; state in `work/<name>/.done/`)
`prepare → calib → pose → lift_free → ball → lift_anch → motion → metrics → plan → render → build → encode`

| stage | script (back / side) | in → out |
|---|---|---|
| prepare | `common/prepare.py`, `common/parse.py` | video + CVAT → `new/fr` frames, `pts.npy`, `labels.pkl`, `job.json` (events, window, fps), label validation report |
| calib | `nl/calib.py` / `sw/prep.py` | labels → `camera.npz` |
| pose | `nl/pose_run.py` / `sw/pose_run2.py` (runs in **mpenv**) | frames + labels → `mp_pose.npz` (L2 33×2, L3 33×3, VIS) |
| lift_free | `nl/lift.py free` / `sw/lift.py free` | → `player3d_free.npz` (X T×18×3) |
| ball | `nl/ball.py` / `sw/ballrun.py free` | → `ball3d.pkl` |
| lift_anch | `lift.py anch` | uses ball contact/toss anchors → `player3d_anch.npz` |
| motion | `nr|nq/motion_lab2.py` | → `motion_nl.pkl` (racket R/butt/head, ball3, roll) |
| metrics | `nr|nq/ana/metrics.py` | → `ana/metrics.json`; then `gen_data.py` writes `ana/data.py` (MET, X, EV, TYPE via `autotext.py`) |
| plan | `nr|nq/plan_all.py` | camera path, trails, fades → `plan_o.json` (orbit), `plan_f.json` (freezes), `plan_l.json` (long shot, **back only**) |
| render | `nr|nq/scene_nr.py` (Blender, `bpy`) + `comp.py` | `ro/rf/rl/t*.png` base+trail layers → glow composite `oo/of/ol/o*.png` |
| build | `nr|nq/ana/build.py <segment>` | slides/overlays → `fin_en/`, `fin_fa/` frames |
| encode | `reel.py` | two-pass x264 EN (<30 MiB), CRF 23 FA |

## 1. Ingest and timing
* `ffmpeg` → PNG frames at native size. Real time = container PTS (`ffprobe -show_entries packet=pts_time`), saved `pts.npy`.
* IMG_7125: variable frame rate, PTS alternates 33/67 ms (≈20 fps real) → all speeds/times use `T_of(frame)` (`ball.py`), never `frame/30`.
* IMG_7122: slow-motion export where each real frame is repeated ~3.33 container frames → detect unique frames by frame difference (`sv/fdiff.npy`, `S.npy`: unique starts 68,71,74,78,…,274). One unique frame = **1/30 s** (verified with ballistics). Reel window = container tc−106 … tc+100 (63 unique frames, tc at index 32).
* Frame-index convention in code: arrays are indexed by *unique-frame index* (side) or *video frame* (back).

## 2. Labels (CVAT for video 1.1)
Tracks: `P_player_skeleton` (22 points: shoulders, elbows, wrists, hips, knees, ankles, heels, foot-index, top/bottom spine, index/thumb), `R_racket…` (10 racket points: tip, head_left/right, string_bed_center, throat_left/right, yoke_center, shaft, handle_top, butt_cap), `R_racket_face` ellipse, `B_ball` ellipse (+ `B_ball_center`), `B_contact_racket` point at the contact frame (exactly one), `B_contact_ground` at bounces, `C_structured_court` points (back view, frame 0; 20 named points). Parsed into `labels.pkl`: `court{name:(2,)}, skel{joint:(T,2)}, rack{pt:(T,2)}, ball{f:(x,y,rx,ry,outside)}, face{f:(cx,cy,w,h,angle)}, contacts[(label,frame,[x,y])]`. See `docs/DATA_FORMATS.md`.
Auto-detected events (job.json): `tc0` = contact label frame; `bounce_f` = last ground contact after tc; `f0` release = walk back from the peak of |ball − left wrist| until the distance returns under 2× the "held" level (10th percentile) → first rising frame (back: +0, side: −3 → a conservative anchor); `ball0` = start of the held run; `ball1` = bounce+2 (back) or tc+1 (side, post-contact ball flight removed); `N` = tc+18 (back) / 63 unique frames (side).

## 3. Camera
**Back view** (`nl/calib.py`): 20 court points with known world coords; parameters p = [f, yaw, pitch, roll, cx, cy, cz] (principal point fixed at image centre); `scipy.least_squares(soft_l1)` multi-start + weak camera-height prior (~1.5 m); **outlier rejection** (points with error > max(20 px, 2.5×median) dropped and refit — near-baseline points are often outside the image). Report `median court reprojection error`; healthy < 15 px. Hand-tuned reference for IMG_7125: f=659, yaw −9.85°, pitch −1.92°, roll 5.11°, centre (1.35,−16.07,1.79); kit auto gives f=657, yaw −9.90°, pitch −1.96°, roll 5.65°.
**Side view** (`sw/prep.py`): court labels unusable → level camera, f = 659 px (same phone), player height H (default 1.80 m, `--height`) with neck at 0.818 H → camera distance D = 2.695 m and height 1.327 m for IMG_7122. For rendering the player is placed 0.5 m behind the baseline (camera y shifted to −12.4).

## 4. Pose and 3D lift
* MediaPipe Pose (model_complexity 1) on a 640 px crop around the labelled skeleton, 1.5× upscaled → world landmarks as **depth prior only** (labels give the 2D). Needs **mediapipe 0.10.14 in Python 3.12** (`mpenv`); 0.10.32 lacks `solutions`.
* `lift.py` (JAX, x64, L-BFGS, SciPy): unknown 3D joints X(T,18,3); losses = reprojection of labels, constant bone lengths (14 groups), depth prior, feet ≥ ground contact, temporal smoothness; `free` pass then `anch` pass with anchors: racket butt/head at contact = ball position, left wrist at the toss release frames f0,f0+1 = ball. Elbow 3D is unreliable near contact → **metrics use the 2D label angle for elbow at contact** (and for elbow at the low point in the back view; side view uses 3D there).

## 5. Ball and racket
`ball.py/ballrun.py`: piecewise ballistic flight (g=−9.81, drag KD=0.02, restitution e_v=0.74, e_h=0.85), unknowns p0, v0, tc, v1 (post-contact velocity), fitted to the reprojection of every labelled ball centre + ball radius (R=0.0335 m) → depth. Soft priors prevent depth drift: toss depth y vs neck (+0.5 m at f0+6, +arm length at f0+12), contact target from the right wrist, speed prior (36±12 m/s back view), side view `v1x` (0,4) and `tcp` pinned to the contact frame. Racket (`motion_lab2.py`): head axis from wrist→head label, roll about the axis by Viterbi over the face-ellipse orientation, blend with the hand near release `(f−(f0−1))/9`; cubic splines (`Motion2`: `jf`, `ball`, `head_at`, `racket`, `tc`).

## 6. Metrics (`ana/metrics.py` → `metrics.json`) and benchmarks (`ana/data.py`)
Events: trophy = max knee flexion in [f0−2 … tc−2] (side: 19–20, override in job.json), low = lowest racket-head z (elbow-flexion point), contact = tc. Measured: front/back knee flexion at trophy, trunk inclination at trophy, elbow flexion at the low point and at contact, shoulder-line tilt at contact (back), contact height, ball speed after contact and net clearance (back), toss apex (height, sideways/forward vs head), landing/lead-foot travel, trophy→contact and low→contact times, side-plane trunk lean, pelvis height timeline (side). Benchmarks `MET[key]` (mean, sd, text): knee_front 64.5±9.7, knee_back 67.4±16.4, trunk 25.0±7.1, elbow_ct 30.1±15.9, elbow_low ≈104 (Fleisig), tilt ≈48, height ≈3.0 m (coach-based), speed ≈183 km/h (Olympic men). `status(m,v)` = ok/low/high with ±1 sd (±0.1 relative when sd is None).

## 7. Auto texts (`code/common/autotext.py`)
From `MET`, `X`, `metrics.json`: strengths (≤3, ordered knees → arm → elbow-low → tilt → toss → height → trunk), priorities (≤3 by |z|), serve-type rows with yellow/orange/grey dots (cue thresholds: back 6 cues — toss sideways, contact sideways, racket motion, net clearance, bounce, speed; side 3 cues — toss forward/back, contact forward/back, racket path), verdict (flat / kick / unsure by vote), `LIMIT` footnote (fps and height from job.json), long-shot rows (back). FA digits through `ui.fa()`.

## 8. Blender scene (`pipeline/scene_skel.py`, `scene_nr.py`)
bpy 5.2.3 LTS, EEVEE, 928×1696, assets `assets/stadium`, `ball`, `racket` (.blend + licences). Skeleton = spheres/cylinders along the 18-joint graph (`data/skeleton_edges.json`), live racket from `Motion2`, ball with the ball path trail, racket-head trail (cyan), camera orbit/freeze from `plan_*.json` (fields: part, tau, cam, target, fov, skel, live_racket, trails, fade, legend[, serve, event, k]). Two render layers per frame: base (`o*.png` after composite) and transparent trail layer `t*.png`; `comp.py` adds the 2D glow. ~6.5–8 s/frame at full quality (draft = `--samples 1`, ~4 s); back ≈ 150 + 144 + 240 frames, side ≈ 150 + 144. **2 CPUs; building segments while rendering can OOM (8 GB) — run `build.py orb` alone.**

## 9. Overlay, slides, timing (`ana/*.py`)
`ui.py` (Layer class, PIL+RAQM, 2× supersampling, fonts `Vazirmatn-{Black,Bold,Medium,Regular}`, palette YEL (255,214,10) CYA GRY ORG), `strings.py` (bilingual strings), `overlay.py` (3D-anchored arcs/dimension lines, stage cards, subject mask `subject_mask`, trail-alpha fading), `slides.py` (model, timeline [side], serve-type check, scorecard, verdict, sources), `build.py` (segments `intro model orb freeze [long|timeline] stype score verdict sources`; schedule from `need(words)=max(2.0, 0.8+words/6.2)` s; orbit time-stretched per stage; freezes hold 40 frames play + hold + 8). The side reel order: `intro model orb freeze timeline stype score verdict sources`; the back reel has `long` instead of `timeline` and its own rows.

## 10. Encode
EN: two-pass libx264 slow, target bitrate computed from duration so the file stays < 27 MiB (cap 4200 kbit/s, maxrate 4500k), yuv420p, faststart. FA: CRF 23 medium. 30 fps, 928×1696.


## Update 2026-11-08 — optional charts, input standards, reliability system
* `--charts auto|off|add|replace`: posture-timeline slide (knee flexion, trunk, pelvis height vs time to contact). Code: `kit/code/common/charts_slide.py` (exec'd at the end of both `slides.py`); segment `timeline` in both `build.py` (order controlled by `job.json: charts` = back `long|both|timeline`, side `timeline|none`). Back view shows trunk-from-vertical + sideways tilt instead of forward lean (depth is unreliable from behind). Time axis uses real timestamps (`tsec`).
* `kit/code/common/qc.py` (stage `qc`, after `metrics`): ~25 checks → `qc.json`/`qc.md`, grade A–D, trust level per reel number. `--qc-badge` prints the grade on the sources slide.
* `code/back/nl/calib.py` now also writes `nl/calib_report.json` (per-point errors, rejected points, leave-one-out and 4 px noise sensitivity).
* `--height` default is now "not given" (1.80 assumed, grade capped); `job.json` keys added: `charts`, `height_given`, `qc_badge`.
* Specification of video/label standards and calibration methods: `docs/INPUT_STANDARDS_AND_CALIBRATION.md` (= kit `INPUT_STANDARDS_AND_CALIBRATION.md`).
* Changing `charts` after a build changes segment start indices: delete `fin_en/` and `fin_fa/` before `--from build`.
