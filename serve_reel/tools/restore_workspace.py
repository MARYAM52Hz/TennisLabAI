#!/usr/bin/env python3
"""Rebuild the original flat workspace layout from the backup (see docs/RESTORE.md).
usage: python3 tools/restore_workspace.py --backup <unzipped backup dir> --ws <new workspace dir> [--inputs <dir with videos>]"""
import argparse, os, shutil, zipfile, re, sys
OLD = '/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
MAP = {'era1/auto': 'auto', 'era1/lab2': 'lab2', 'era1/ana': 'ana', 'era1/rest': 'rest', 'era1/ns_side_v1': 'ns', 'shared/pipeline': 'pipeline', 'shared/data': 'data',
       'era2_back/nl': 'nl', 'era2_back/nr': 'nr', 'era2_back/new_labels': 'new/cvat', 'era3_side/sv': 'sv', 'era3_side/sw': 'sw', 'era3_side/nq': 'nq'}
ap = argparse.ArgumentParser(); ap.add_argument('--backup', required=True); ap.add_argument('--ws', required=True); ap.add_argument('--inputs'); a = ap.parse_args()
ws = os.path.abspath(a.ws); os.makedirs(ws, exist_ok=True)
for src, dst in MAP.items():
    SRC = 'src' if os.path.isdir(os.path.join(a.backup, 'src')) else 'archive'
    s = os.path.join(a.backup, SRC, src)
    if os.path.isdir(s): shutil.copytree(s, os.path.join(ws, dst), dirs_exist_ok=True)
for f in ('REQ_NOTES.md', 'bpy_install.log'):
    p = os.path.join(a.backup, 'src' if os.path.isdir(os.path.join(a.backup, 'src')) else 'archive', f)
    if os.path.exists(p): shutil.copy(p, ws)
n = 0
for dp, dn, fn in os.walk(ws):                         # rewrite the hard-coded scratchpad path in text files
    for f in fn:
        if f.endswith(('.py', '.sh', '.json', '.md', '.txt')):
            p = os.path.join(dp, f)
            try: t = open(p, encoding='utf-8').read()
            except Exception: continue
            if OLD in t: open(p, 'w', encoding='utf-8').write(t.replace(OLD, ws)); n += 1
print('rewrote paths in', n, 'files')
kit = os.path.join(a.backup, 'kit', 'tennis-reel-kit.zip'); kdir = os.path.join(a.backup, 'kit')
if os.path.exists(kit) or os.path.exists(os.path.join(kdir, 'reel.py')):
    if os.path.exists(kit): tmp = os.path.join(ws, '_kit'); zipfile.ZipFile(kit).extractall(tmp); k = os.path.join(tmp, 'tennis-reel-kit')
    else: tmp = kdir; k = kdir
    shutil.copytree(os.path.join(k, 'assets'), os.path.join(ws, 'assets'), dirs_exist_ok=True)
    ft = os.path.join(ws, 'fonts_vz', 'fonts', 'ttf'); os.makedirs(ft, exist_ok=True)
    for f in os.listdir(os.path.join(k, 'fonts')): shutil.copy(os.path.join(k, 'fonts', f), ft)
    print('assets and fonts restored from the kit; full kit is in', tmp)
if a.inputs and os.path.isdir(a.inputs):
    for f in os.listdir(a.inputs):
        if f.upper().endswith('.MOV'): os.makedirs(os.path.join(ws, 'videos'), exist_ok=True); shutil.copy(os.path.join(a.inputs, f), os.path.join(ws, 'videos', f))
print('\nNext (examples):\n  ffmpeg -i videos/IMG_7125.MOV new/fr/f%04d.png        # back view frames (f0001 = frame 0)\n  python3 -I nl/calib.py                                 # then nl/pose_run.py (mpenv), nl/lift.py, nl/ball.py, nr/...\nSee docs/PIPELINE.md and the chain*.sh files.')
