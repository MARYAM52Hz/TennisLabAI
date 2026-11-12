# Restore guide
1. Download all parts into one folder. Verify: `sha256sum -c tennis_bk_SHA256SUMS.txt`.
2. `unzip the repository -d tennis-project && cd tennis-project` (this README, docs, src, kit, tools, transcript). Unzip the other parts into `inputs/` and `outputs/` as you like (`unzip tennis_bk_02_inputs_core.zip -d inputs`, …).
3. **Kit (recommended)**: `unzip kit/tennis-reel-kit.zip` → follow README §2. Needs ffmpeg, Python ≥3.10, libraqm; `setup.sh` builds `venv` and `mpenv`.
4. **Old flat workspace** (to reproduce the delivered reels or read era code in its original layout):
   `python3 tools/restore_workspace.py --backup . --ws ~/tennis_ws`
   The tool copies each `archive/...` folder back to its original name (`nl nr nq sw sv ns lab2 auto ana pipeline data rest new/cvat`), rewrites the hard-coded scratchpad path in scripts to your `--ws`, unpacks assets and fonts from the kit, copies the videos from `inputs` if present, and prints the commands to regenerate frames (`ffmpeg -i IMG_7125.MOV new/fr/f%04d.png` etc.). Then run e.g. `cd ~/tennis_ws && python3 -I nl/calib.py` (see `archive/era2_back/nr/chain.sh`, `archive/era3_side/nq/chain*.sh` for the render chains).
5. Regenerate heavy intermediates only if needed: frames (ffmpeg), `mpenv` (`python3.12 -m venv mpenv && mpenv/bin/pip install mediapipe==0.10.14 numpy==1.26.4 opencv-python-headless`), renders (`scene_nr.py`), final frames (`build.py`).
6. Python packages (main env): `bpy==5.2.*` (needs Python 3.13), `jax==0.12.*`, `scipy`, `numpy`, `opencv-python`, `pillow` (+ libraqm system lib), plus `ffmpeg`.
7. The original session transcript is in `transcript/` (JSONL, last part of the work: kit packaging); earlier sessions are only available through `archive/era1/rest/cmds.json`.
