Tennis reel pipeline v1 (serve2)
1) cvat xml -> labels2d.npz            (pipeline/01_cvat_to_npz.py)
2) court -> camera (K,R,C)              (pipeline/02*_calibrate*.py)  mean err ~6px
3) 2D -> 3D body/racket/ball            (lift_joint.py, lift_racket.py, lift_ball.py)
4) Blender scene + camera + lights      python3 build_scene_v2.py data scene_v2.blend --frames 133   (needs: pip install bpy)
5) Still render                         python3 render_still.py scene_v2.blend cam_match 74 out.png
Cameras in scene: cam_match (original view), cam_front34, cam_behind, cam_opposite.
World: metres, origin = net centre, x along net, y toward far baseline, z up.
