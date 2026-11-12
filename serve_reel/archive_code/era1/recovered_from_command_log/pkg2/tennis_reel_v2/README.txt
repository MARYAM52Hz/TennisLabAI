Serve reel pipeline v2
1. CVAT xml -> labels2d.npz            01_cvat_to_npz.py
2. court -> camera                     02*_calibrate*.py
3. 2D -> 3D (body, racket, ball)       03_lift_body.py, 04_racket.py, lift_ball.py, then
   lift_joint2.py data --out _ext      (adds elbow/knee extension prior: fixes folded arms from depth ambiguity)
4. scene                               build_scene_v3.py data scene_v3.blend --frames 92   (pip install bpy scipy)
5. frames + 2D anchors                 render_cp.py scene.blend jobs.json outdir   (jobs: frame, az, el, dist, lens, tgt)
6. HUD + video                         reel.py seq_dir out.mp4   (all text/labels in CONFIG at top)
Run python with -I and not from a folder containing files named like stdlib modules.
