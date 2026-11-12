# Standards, decisions and lessons

## A. User requirements (chronological, all still in force)
1. (Oct 24) Handle **@tennismad.ai** in every reel, on every frame; text cards held long enough to read carefully. Original rule in `REQ_NOTES.md`: hold ≥ 1.2 s + 0.40 s/word (FA) / 0.32 s/word (EN), min 2.5 s; the later, faster rhythm uses `need(words)=max(2.0,0.8+words/6.2)`.
2. Validate and show the **serve type** (flat vs kick): IMG_2772 serve 1 = flat, serve 2 = kick. Final table: "flat/kick" labels must not overlap (moved one line down).
3. FA version is less important; **EN at the best possible quality for upload** (< 30 MiB).
4. IMG_7125: faster rhythm than the 152 s reel; text cards not too long.
5. Toss depth: the ball is about an arm-length *in front of the body*, not over the head → depth priors (see PIPELINE §5).
6. Text cards must not cover the subject: translucent cards, auto-fade under the subject mask, ball/racket trails.
7. Annotation colour yellow.
8. IMG_7122: court labels invalid → no court use; only **posture and stroke style**, no long shots, clearly different from back-view reels.
9. (Nov 1) Package everything so a friend gives only video + labels and gets the reel → kit + skill. (Nov 8) Full backup + README.

## B. Key design decisions and why
* **Kit + thin skill** instead of skill only: a skill is just instructions; the pipeline needs Blender, MediaPipe (separate py3.12 venv), JAX, ffmpeg and ≈1 h rendering. The skill (`tennis-serve-reel`) tells Claude how to run/verify the kit.
* **MediaPipe only as depth prior**: the 2D comes from the user's labels (more accurate); constant bone lengths + feet on ground make the lift stable.
* **Ballistic fit with soft priors** instead of free triangulation: single camera cannot see depth; the ball radius and gravity give depth; priors stop drift.
* **2D elbow at contact**: the 3D lift gave 73° for an almost straight arm (image shows ≈18°).
* **Side view posture-only**: only in-plane metrics (trunk lean, knee flexion, elbow, pelvis height, toss/contact relative to the head, lead-foot travel); no net clearance/bounce/ball speed.
* **Subject mask + alpha fade** so overlays never hide the athlete; **2× supersampled** PIL layers for crisp Persian text.
* **Draft mode** (`--samples 1`) for fast tests; full-quality uses the default sample count.

## C. Lessons / bugs already fixed (do not re-introduce)
| symptom | cause | fix |
|---|---|---|
| speeds/times wrong | assumed 30 fps; clip is VFR (33/67 ms) | use `pts.npy` timestamps |
| side clip stutter, wrong speeds | slow-mo export repeats frames ~3.33× | unique-frame detection, 1/30 s each |
| toss over head | free depth fit | priors on toss depth (neck y + 0.5 m / + arm length) |
| frame mismatch by 1 | `ffmpeg` names `f0001` = frame 0 | index with `f{S+1}` |
| player at the net (y=0) in side view | prep placed player at origin | camera y shifted to −12.4 (render only) |
| 3D elbow 73° at contact | lift ambiguity | 2D label angle |
| long-shot hold black frame | held a faded last frame | hold frame 207 of the sequence |
| legend "SERVE 1/2" in a single-serve reel; `rows {2:4}` IndexError | copied from the two-serve code | legend/rows fixed in `comp.py` |
| `build.py orb` killed (OOM, 8 GB) | cache of 600 overlays + concurrent render | cache limit 40; run alone |
| nq chain overwrote IMG_7125 output | script still pointed at `nr/` | paths fixed (`sed s#nr/#nq/#g`) |
| `slides.py` edit deleted a block | `index()` hit the old TROWS definition | restore from `slides_v1.py`, use last-occurrence indices |
| duplicate code in `ball.py` | concurrent edit by another session | always re-read before patching |
| `pkill -f chain.sh` killed my shell | pattern matched caller | poll the log for `ALLDONE` |
| kit back calibration gave f=677, trunk 16° | near-baseline court points outside image, soft_l1 not enough | outlier rejection + refit (f=657) |
| `autotext` crash in side `rows()` | lambda returned a tuple of tuples wrongly | parenthesised |

## D. Reference numbers of the delivered reels (for regression tests)
IMG_7125 (hand-tuned calibration): contact frame 74.87, front/back knee 55/72°, trunk 7°, elbow low 84°, elbow contact 11°, shoulder tilt 43°, height 2.74 m, speed 120 km/h, trophy→contact 429 ms, low→contact 196 ms. Kit auto calibration: knees 55/69°, trunk 17°, tilt 42°, height 2.77 m, speed 120 km/h.
IMG_7122 (kit reproduces): front/back knee 69/35°, trunk 11°, elbow low 95° (3D), elbow contact 18° (2D), height 2.77 m, trophy→contact 433 ms, low→contact 167 ms, toss apex 3.26 m, contact 15 cm ahead of the head, toss apex 43 cm ahead of the head, lead-foot travel 44 cm, racket path +2°.


## Update 2026-11-08 — optional charts, input standards, reliability system
* `--charts auto|off|add|replace`: posture-timeline slide (knee flexion, trunk, pelvis height vs time to contact). Code: `kit/code/common/charts_slide.py` (exec'd at the end of both `slides.py`); segment `timeline` in both `build.py` (order controlled by `job.json: charts` = back `long|both|timeline`, side `timeline|none`). Back view shows trunk-from-vertical + sideways tilt instead of forward lean (depth is unreliable from behind). Time axis uses real timestamps (`tsec`).
* `kit/code/common/qc.py` (stage `qc`, after `metrics`): ~25 checks → `qc.json`/`qc.md`, grade A–D, trust level per reel number. `--qc-badge` prints the grade on the sources slide.
* `code/back/nl/calib.py` now also writes `nl/calib_report.json` (per-point errors, rejected points, leave-one-out and 4 px noise sensitivity).
* `--height` default is now "not given" (1.80 assumed, grade capped); `job.json` keys added: `charts`, `height_given`, `qc_badge`.
* Specification of video/label standards and calibration methods: `docs/INPUT_STANDARDS_AND_CALIBRATION.md` (= kit `INPUT_STANDARDS_AND_CALIBRATION.md`).
* Changing `charts` after a build changes segment start indices: delete `fin_en/` and `fin_fa/` before `--from build`.
