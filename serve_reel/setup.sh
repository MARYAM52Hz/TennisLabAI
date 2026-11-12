#!/usr/bin/env bash
# One-time setup. Needs: Linux/macOS, Python 3.10-3.13, ffmpeg, and ~3 GB free disk.
# Creates ./venv (main stack: Blender-as-a-module, jax, scipy, opencv, pillow) and ./mpenv (Python 3.12 + mediapipe 0.10.14 for pose detection).
set -e
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo "Install ffmpeg first (apt install ffmpeg / brew install ffmpeg)"; exit 1; }
PYMAIN=${PYMAIN:-python3}
$PYMAIN -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q bpy==5.2.3 numpy scipy "jax[cpu]" opencv-python-headless pillow
# Persian text shaping needs Pillow built with libraqm (Linux: apt install libraqm0 ; macOS: brew install libraqm)
PY312=${PY312:-$(command -v python3.12 || true)}
if [ -z "$PY312" ]; then echo "python3.12 not found: install it (mediapipe 0.10.14 needs <=3.12) or set PY312=/path/to/python3.12"; exit 1; fi
$PY312 -m venv mpenv
./mpenv/bin/pip install -q --upgrade pip
./mpenv/bin/pip install -q mediapipe==0.10.14 numpy==1.26.4 opencv-python-headless
echo "Checking..."; ./venv/bin/python reel.py check
echo
echo "Run:  ./venv/bin/python reel.py make --view back --video clip.MOV --labels cvat.zip --name myserve"
