# serve_reel — tennis serve video + CVAT labels → Instagram analysis reel

Module of **TennisLabAI**. Turns a phone video of a tennis serve plus hand labels (CVAT) into a vertical analysis reel (EN + FA): 3D Blender reconstruction, trails, orbit, key-position freezes, scorecard against the biomechanics literature, optional posture charts, serve-type check and a reliability grade. It is the *markerless single-camera* branch of the framework (see `docs/architecture.md`): pose lifted from one RGB phone camera, scale from court points / player height / ball gravity, quality gated by an explicit reliability score.

## Where things are
| path | what |
|---|---|
| `serve_reel/reel.py` | the one-command driver (`check`, `make`) |
| `serve_reel/code/{back,side,common}` | analysis + render code per camera view, shared auto-text / QC / charts |
| `serve_reel/LABELING.md` | CVAT labelling guide |
| `serve_reel/INPUT_STANDARDS_AND_CALIBRATION.md` | **video + label standards, scale calibration (with/without labels, human error), fact-checks, reliability system** (also in `docs/serve_reel/`) |
| `serve_reel/examples/` | two real CVAT exports (back view, side view) with user names removed |
| `serve_reel/archive_code/` | code of the three earlier project eras, for reproduction (no data) |
| `serve_reel/tools/restore_workspace.py` | rebuilds the old flat workspace from the archive (see `docs/serve_reel/RESTORE.md`) |
| `docs/serve_reel/` | PIPELINE, DATA_FORMATS, STANDARDS_AND_DECISIONS, HISTORY_AND_INVENTORY, EXTENDING, RESTORE, INPUT_STANDARDS |
| `serve_reel/assets/` | Blender stadium / ball / racket with their licences (stadium is CC BY 3.0: credit required; see `assets/README_ASSETS.md`) |

> Path note: the docs in `docs/serve_reel/` were written for the stand-alone repository where `kit/` = this `serve_reel/` and `archive/` = `serve_reel/archive_code/`.

---

# tennis-reel-kit — serve video + CVAT labels → Instagram analysis reel

**You give:** one serve video + the CVAT labels of that video.
**You get:** a ~90 s vertical reel (EN, under 30 MiB, and FA) with the 3D Blender reconstruction, glowing ball/racket trails, orbit camera, key-position freezes, a scorecard against the literature, a serve-type check and the sources — with the `@handle` on every frame.

Two views are supported (pick with `--view`):

| view | camera | needs | reel content |
|---|---|---|---|
| `back` | behind the baseline, court lines visible | court points labelled on frame 0 | posture + ball path + contact height + ball speed + net clearance |
| `side` | at the side of the player (court NOT needed) | player's real height (`--height`) | posture/stroke style only (knees, trunk lean, elbow, toss/contact vs head, posture timeline) |

## 1. Install (once, ~15 min, ~3 GB)
Linux or macOS, Python 3.10–3.13 (the pose step needs a separate Python 3.12), ffmpeg.
```
./setup.sh            # creates ./venv and ./mpenv, then runs the check
./venv/bin/python reel.py check
```
Persian text needs Pillow with libraqm (`apt install libraqm0` / `brew install libraqm`). No GPU needed.
Windows: use WSL2 (Ubuntu) and follow the Linux steps.

## 2. Run (one command)
```
./venv/bin/python reel.py make --view back --video IMG_7125.MOV --labels cvat_export.zip --name serve1
./venv/bin/python reel.py make --view side --video IMG_7122.MOV --labels cvat_export.zip --name serve2 --height 1.80
```
Options: `--height 1.82` (player height in m: the scale in the side view and an independent cross-check in the back view — always give it), `--charts auto|off|add|replace` (posture-timeline charts slide; default on for the side view; for the back view `add` = long shot + charts, `replace` = charts instead of the long shot), `--qc-badge` (print the reliability grade on the sources slide), `--hand auto|right|left` (racket hand; auto-detected, left-handers are mirrored), `--handle @yourpage` (default `@tennismad.ai`), `--draft` (≈2× faster, slightly noisier render for a quick look), `--out DIR`, `--work DIR`.
Result: `output/<name>_reel_EN.mp4` (two-pass x264, always < 30 MiB) and `output/<name>_reel_FA.mp4`.
Time on a 2-CPU machine: ~5 min of analysis + 35–60 min of rendering (back view renders more frames than side view). If anything stops, run the **same command again**: finished stages and rendered frames are skipped.
Logs: `work/<name>/logs/*.log`. Everything the pipeline found is in `work/<name>/job.json` (frames of release/contact/bounce…, auto-detected).
Edit `job.json` and re-run with `--from <stage>` (stages: prepare calib pose lift_free ball lift_anch motion metrics plan render build encode) to override a detection.

## 3. Labels (CVAT, "CVAT for video 1.1" export, zip or annotations.xml)
See `LABELING.md`. In short: skeleton on every frame of the serve, racket skeleton + racket-face ellipse on every frame, the ball ellipse from the toss to the end of the clip, ONE `B_contact_racket` point at the contact frame, and for the back view `B_contact_ground` at the bounce plus the 16 court points on frame 0. The kit validates the export first and lists everything that is missing before any heavy step runs.

## 4. What is automatic and what is an estimate (read this before publishing)
Automatic: frame extraction, slow-motion duplicate-frame detection (side view), timestamps (variable frame rate), release/contact/bounce detection from the labels, camera calibration (back: from the court points; side: from the player's height), pose lifting to 3D, ball trajectory fit, racket orientation, all numbers and all texts (strengths, priorities, serve-type verdict) of the reel.
Estimates, not measurements: one camera only. Typical angle error ±10–15°, ball speed ±10 %. The back-view result is **sensitive to the court calibration** (on the IMG_7125 test clip the earlier hand-tuned calibration gave a trunk tilt of 7° at the trophy and the kit's automatic calibration gives 17°; all other numbers moved by ≤ 3°), so check the "median court reprojection error" line in `logs/calib.log` (should be < 15 px) and look at the first frames of the orbit. The side view assumes the same phone as the back-view test clips (focal ≈ 0.515 × image height) and a level camera. Reference values come from heterogeneous studies (Frontiers 2024 meta-analysis, Fleisig 2003, …) and are guidance, not norms.
The serve-type verdict (flat/kick) is a simple rule on 3 (side) or 6 (back) cues; "unsure" is a valid result.
Tested on exactly two clips (IMG_7125 back, IMG_7122 side, iPhone, 720×1280). Other phones, resolutions, left-handed players, or two serves in one clip are untested.

### 4b. Input standards, calibration, reliability grade
Full specification — video standard, label properties, scale-calibration methods with/without labels and against human error, the fact-check list, and the A–D reliability system — is in **[INPUT_STANDARDS_AND_CALIBRATION.md](INPUT_STANDARDS_AND_CALIBRATION.md)** (Persian + English summaries). After the `metrics` stage the kit writes `work/<name>/qc.json` and `qc.md` (grade, per-number trust level, what to fix first) and prints a summary; re-run on its own with `REEL_JOB=work/<name> python3 -I code/common/qc.py`.

## 5. Layout
`reel.py` driver · `code/back|side` pipelines · `code/common` (label parser, auto-detection, automatic texts) · `assets/` (stadium, ball, racket Blender models, licences inside) · `fonts/` (Vazirmatn, OFL) · `examples/` (the two CVAT exports used for testing).

---
# فارسی (خلاصه)

> **جدید:** گزینه‌ی `--charts` (نمودار پاسچر اختیاری برای همه‌ی ریل‌ها)، `--height` (قد واقعی بازیکن؛ حتماً بدهید)، `--qc-badge` و مرحله‌ی `qc` که نمره‌ی اعتماد A تا D و سطح اعتماد هر عدد را می‌دهد. توضیح کامل استاندارد فیلم، لیبل، کالیبراسیون و فکت‌چک: `INPUT_STANDARDS_AND_CALIBRATION.md`.
**ورودی:** یک ویدیوی سرو + فایل لیبل CVAT همان ویدیو. **خروجی:** ریل عمودی ~۹۰ ثانیه (نسخه‌ی EN زیر ۳۰ مگابایت و نسخه‌ی FA) با بازسازی سه‌بعدی در بلندر، مسیر توپ و راکت، چرخش دوربین، فریزهای کلیدی، کارنامه در برابر منابع علمی، اعتبارسنجی نوع سرویس و منابع؛ آیدی پیج روی همه‌ی فریم‌ها.

۱. نصب (یک بار): `./setup.sh` سپس `./venv/bin/python reel.py check`.
۲. اجرا: دستورهای بخش Run بالا. `--view back` برای دوربین پشت خط (نقاط زمین لازم است) و `--view side` برای دوربین کنار (فقط قد بازیکن با `--height`؛ فقط پوسچر و سبک ضربه). اگر وسط کار قطع شد همان دستور را دوباره اجرا کن؛ ادامه می‌دهد.
۳. لیبل‌گذاری: `LABELING.md`. قبل از هر کار سنگین، کیت لیبل‌ها را بررسی می‌کند و همه‌ی کمبودها را یک‌جا گزارش می‌دهد.
۴. محدودیت‌ها: دوربین تکی؛ خطای زاویه ±۱۰ تا ۱۵° و سرعت ±۱۰٪. نمای پشت‌سر به کالیبراسیون زمین حساس است (خط `median court reprojection error` را ببین). فقط روی دو کلیپ (آیفون، ۷۲۰×۱۲۸۰) تست شده است.
