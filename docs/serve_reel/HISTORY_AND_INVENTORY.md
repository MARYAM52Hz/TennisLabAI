# History and inventory

## Inputs → label sets
| video | frames / size | label export | notes |
|---|---|---|---|
| `IMG_2772.MOV` | 237 fr, 464×848 | `task_1886128_annotations_2026_09_10_…cvat_for_video_1.1.zip` (23 labels, 443 tracks: court lines per frame, skeleton, ball, racket, contacts) | two serves; hand-held |
| `IMG_7125.MOV` | 133 fr (serve 0–91), 720×1280 | `0ca3a477-1.zip` (final); `job_4439304_annotations_2026_09_03_…zip` = earlier export of the same clip | back view, VFR |
| `IMG_7122.MOV` | 276 fr, 720×1280 | `4ac1bf28-1_1.zip` | side view, slow-motion duplicates; court labels there are NOT valid |
Other uploads: `tennis_reel_v1.zip` (Oct 13 prototype), Blender assets (`Tennis_Stadium_Updated..zip`, `wireframe_essentials.zip`, `Tennis_Raquet.zip`, `tennis_ball_in_cycles.zip`, `Human_Male_Base_Mesh_with_armature.zip`), reference videos (Jannik Sinner forehand checkpoints, serve2_* annotated videos, mannequin/stadium experiments, `serve_reel_v2.mp4`, validation_checkpoints.png, attachment.txt = earlier assistant message).

## Delivered reels
| file (in backup) | clip | length | notes |
|---|---|---|---|
| `out_IMG2772_EN` (= `serve_analysis_EN_best.mp4`) | IMG_2772 | 152.6 s | final EN, 28.4 MB, handle on all frames |
| `out_IMG2772_FA` (= `serve_analysis_final_fa.mp4`) | IMG_2772 | 152.6 s | final FA 20.4 MB |
| `IMG7125_serve_analysis_EN/FA.mp4` | IMG_7125 | 95.6 s | back view, one flat serve |
| `IMG7122_posture_analysis_EN_hq.mp4`, `_FA.mp4` | IMG_7122 | 88.3 s | final posture-only side view |
| `IMG7122_serve_analysis_EN/FA.mp4` | IMG_7122 | 93.6 s | superseded v1 (court/ball numbers) |
Omitted (superseded): `serve_analysis_{en,fa}.mp4` (57.6 s first versions), `serve_analysis_v2_*`, `serve_analysis_v3_*`, `serve_analysis_final_en.mp4`, `IMG7122_posture_analysis_EN.mp4` (lower-bitrate twin of EN_hq).

## Source tree map (backup `archive/` ← original scratchpad dir)
| backup path | original | what |
|---|---|---|
| `era1/auto` | `auto/` | automatic (label-free) experiments: stabilization, person tracking, MediaPipe pose, raw calibration |
| `era1/lab2` | `lab2/` | label-driven IMG_2772: `parse2, calib_lab, register, lift_lab, ball_lab, motion_lab(2)`, small pkl/npz |
| `era1/ana` | `ana/` | IMG_2772 slides/overlay/build (`build2.py` = final builder), `metrics.py/json`, `stype*.py` |
| `era1/rest` | `rest/` | `cmds.json` = command log of earlier sessions; `rebuild.py`/`replay.py` replay file writes |
| `era1/recovered_from_command_log` | – | 63 scripts re-extracted from the log (lab3 render plan/scene/comp, auto/*, athlete/*, pipeline/*, tools/*). Patches applied later by sed/python in the log are NOT applied; best-effort |
| `era1/ns_side_v1` | `ns/` | first side-view reel (v1) code/plans |
| `shared/pipeline`, `shared/data` | `pipeline/`, `data/` | `scene_skel.py` (Blender scene builder), `motion.py`, `skeleton_edges.json` |
| `era2_back/nl`, `nr`, `new_labels` | `nl/ nr/ new/cvat` | IMG_7125 analysis (`nl`) and reel (`nr`), CVAT xml |
| `era3_side/sv sw nq` | `sv/ sw/ nq/` | IMG_7122: raw handling (`sv`), data prep/analysis (`sw`), posture reel (`nq`) |
| `other_session_nw` | `nw/` | an older parallel pipeline for IMG_7125 by another session (reference only) |
Original files not copied: frames (`raw/ new/fr sv/fr`), renders (`ro rf rl oo of ol fin_*`), `mpenv`, `whl`, `auto/stab.npy` (280 MB), `auto/masks.npy`, plan jsons > 6 MB (regenerable by `plan_all.py`).

## Approximate time costs
Analysis stages ≈ 5 min total; Blender render 35–60 min (2 CPUs, full) — back ≈ 534 frames, side ≈ 294; build 8–15 min; encode 3 min.
