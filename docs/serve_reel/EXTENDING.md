# Guide for developers and AI assistants

## Ground rules
1. Read README §7e (never touch) first. Run every change on **both** reference clips (`examples/*.xml` in the kit) in `--draft` and compare `metrics.json` with docs/STANDARDS_AND_DECISIONS.md §D.
2. Look at output frames (contact sheet of ≥ 8 frames) — numbers alone do not catch overlapping text.
3. Keep the kit and the old flat code in sync only through the kit: the kit is the maintained line (`code/back`, `code/side`, `code/common`). Era code is archival.
4. Python is run isolated (`-I`); scripts get paths from `REEL_JOB`; per-video numbers come from `job.json` (`JC[...]`); never hard-code a frame number.
5. Texts: bilingual pairs `(fa, en)`; Persian digits via `ui.fa()`; test long Persian lines for wrapping.
6. Re-read a file immediately before patching if several agents share the folder.

## Recipes
**Add a metric** — (1) compute it in `ana/metrics.py` and store in `metrics.json`; (2) add a `MET` entry (label pair, mean, sd, `A`) in `code/common/data_*.tpl` and fill it in `gen_data.py`; (3) add the label to `ana/strings.py`; (4) show it: scorecard rows in `slides.py` (`ROWS`), optional on-body arc in `overlay.py`; (5) strengths/priorities text in `autotext.py`.
**Add/replace a language** — duplicate each `(fa,en)` pair to a triple in `strings.py`, `autotext.py`, `slides.py`; add a font if non-Latin; add a language to `LANGS` in `build.py` and an encode in `reel.py`.
**Change the timeline** — `build.py` constants (`ORDER`, `N[...]`, `need`, `GW`, `FW`, `ST_ROW`, `VER_*`); `N` values define the total length; `START` is derived.
**Another benchmark set (e.g. women, juniors)** — `MET[...]['mean'/'sd']` in the templates; keep citations in `slides.py` sources list.
**Left-handed player** — untested: mirror x of labels before processing (labels → `parse`), or add `hand='left'` and swap left/right joint names in `lift.py/metrics.py` (anchors use right wrist for contact and left for toss).
**Two serves in one clip** — the single-serve code assumes one `B_contact_racket`; era 1 code (`lab2/ball_lab.py`, `ana/build2.py`) shows the two-serve variant (A/B segments, serve legend).
**New view (e.g. front/oblique)** — add `code/<view>/` with the same stage scripts: a calibration producing `camera.npz` (K,R,cam), pose+lift reusable, `ball.py` priors for the new geometry, a `metrics.py` that only uses measurable quantities, `plan_all.py` cameras, a `data_<view>.tpl`; register stages in `reel.py` (`STAGES_*`, `render()` plan list) and `prepare.py` (event detection). Decide *first* which numbers are trustworthy from that view (see side-view decision).
**Faster/better render** — `--samples`, resolution `W,H` in `ui.py` and `scene_nr.py` must change together; EEVEE settings are in `scene_nr.py`; GPU Blender would cut render time but bpy GPU is untested here.
**Better calibration (back view)** — add more court points, a per-frame refinement for hand-held clips (`lab2/register.py` is the era-1 solution), or free principal point.

## Ideas not done yet
Automatic court-point detection; automatic ball detection to reduce labelling; two-camera fusion; per-frame uncertainty display; shot-type classifier trained on labelled serves; Docker image of the kit; Windows-native setup; CI test on the two example clips (draft mode, compare `metrics.json` within tolerance).

## Prompts for another AI assistant
"You are extending tennis-reel-kit. Read README.md (esp. §5 standards and §7e never-touch) and docs/PIPELINE.md. Do not change time-base, calibration constants, ballistic priors or standards. Implement <feature> in `code/...`, run the draft test on both example clips, show a contact sheet of the frames you changed, and report metrics differences versus docs/STANDARDS_AND_DECISIONS.md §D."


## Update 2026-11-08 — optional charts, input standards, reliability system
* `--charts auto|off|add|replace`: posture-timeline slide (knee flexion, trunk, pelvis height vs time to contact). Code: `kit/code/common/charts_slide.py` (exec'd at the end of both `slides.py`); segment `timeline` in both `build.py` (order controlled by `job.json: charts` = back `long|both|timeline`, side `timeline|none`). Back view shows trunk-from-vertical + sideways tilt instead of forward lean (depth is unreliable from behind). Time axis uses real timestamps (`tsec`).
* `kit/code/common/qc.py` (stage `qc`, after `metrics`): ~25 checks → `qc.json`/`qc.md`, grade A–D, trust level per reel number. `--qc-badge` prints the grade on the sources slide.
* `code/back/nl/calib.py` now also writes `nl/calib_report.json` (per-point errors, rejected points, leave-one-out and 4 px noise sensitivity).
* `--height` default is now "not given" (1.80 assumed, grade capped); `job.json` keys added: `charts`, `height_given`, `qc_badge`.
* Specification of video/label standards and calibration methods: `docs/INPUT_STANDARDS_AND_CALIBRATION.md` (= kit `INPUT_STANDARDS_AND_CALIBRATION.md`).
* Changing `charts` after a build changes segment start indices: delete `fin_en/` and `fin_fa/` before `--from build`.
