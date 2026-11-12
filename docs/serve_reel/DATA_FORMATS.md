# Data formats (all arrays numpy, metres/pixels as noted)

| file | structure |
|---|---|
| `job.json` (kit) | `view, name, W, H, labels_xml, labels_pkl, T_lab (label frames), player_h, ana ("nr/ana"\|"nq/ana"), video_frames, N (frames used), tc0 (contact frame), f0 (release), ball0, ball1, bounce_f (null on side), st0/st1 (stage thresholds), trophy_w0/w1, focal (side 659), fps_real, cadence (side ≈3.33 container frames per unique), player_y (side −12.4), container_tc, optional `overrides` (e.g. trophy/low), optional `camera_npz` (test-only camera override)` |
| `labels.pkl` | `court{name:(x,y)}` (frame 0, back only) · `skel{joint:(T,2)}` 22 joints · `rack{point:(T,2)}` 10 points · `ball{frame:(cx,cy,rx,ry,outside)}` · `ballc{}` · `face{frame:(cx,cy,w,h,angle_deg)}` · `contacts[(label,frame,[x,y])]` |
| `pts.npy` | (T,) real timestamps in seconds per frame (back: container PTS; side: uniform 1/30 per unique frame) |
| `S.npy` (side) | container frame index of each unique frame inside the window |
| `camera.npz` | `K(3,3), R(3,3), cam(3,)` world→camera; back also `p(7)=[f,yaw,pitch,roll,cx,cy,cz]` |
| `mp_pose.npz` | `L2 (T,33,2)` px, `L3 (T,33,3)` MediaPipe world, `VIS (T,33)` |
| `player3d_free.npz` / `player3d_anch.npz` | `X (T,18,3)` world joints; `names` = left/right shoulder, elbow, wrist, hip, knee, ankle, heel, foot_index, top_spine, bottom_spine (18); `lengths (14)` constant bone lengths of groups `upper_arm forearm thigh shank ank_heel ank_toe heel_toe sh_w hip_w torso x_torso spine ts_sh bs_hip` |
| `ball3d.pkl` | `{'S': {f0 int, p0(3) release position, v0(3), tc seconds after f0, v1(3) post-contact velocity, cost}}` |
| `motion_nl.pkl` | `Rr (T,3,3)` racket rotation, `butt (T,3)`, `head_c (T,3)`, `axis (T,3)`, `ball3 (T,3)`, `ball_ok (T)`, `head_px (T,2)`, `roll_cost (T)`, `tc` (float frame), `launch_v (3)` |
| `plan_{o,f,l}.json` | `{'frames':[{part,tau (fractional frame),cam [x,y,z],target,fov,skel,live_racket,trails{ball:[a,b],racket:[a,b]},fade,legend[,serve,event,k]}],'pivot'}` — one entry per rendered frame |
| `ro/rf/rl/tNNNN.png` | RGBA trail layer (alpha = glow source), `oo/of/ol/oNNNN.png` composite frames 928×1696 |
| `metrics.json` | `events{trophy,low,contact,landing}`, `times_ms{trophy_to_contact,low_to_contact}`, `trophy{kneeFront,kneeBack,trunkInc,shTilt}`, `low{elbow2D,elbow3D,rackZ}`, `contact{ballXYZ,height,ahead,elbow2D,(elbow3D),shTilt,trunkInc,ball_minus_neck_x | ball_ahead_of_head,pelvisZ,(headY)}`, `toss{apexFrame,apexZ,apex_minus_neck_x | apex_ahead_of_head,apex_to_contact_ms,…}`, `ball{speed_kmh,launch_deg,net_clear,bounce_xy,…}`, `racket_2d` (back) / `racket{path_up_deg,head_speed_ms,…}` (side), `landing{frame,left_foot_y,into_court}`, `foot_at_toss_y` |
| `ana/data.py` (generated) | `TC, EV{trophy,low,contact,landing}, STAGES, stage_of(tau), MET{key:{label fa/en, mean, sd, A, B, …}}, status(), X{'A':{t_tc,t_low,ahead,landing,rise,toss_apex[,lean],chain}}` |
| `fin_en/`, `fin_fa/` | `fNNNNN.png` final frames (30 fps), encoded by `reel.py encode` |

Coordinate notes: back view world x along the net (right in image), y away from camera, z up; side view x toward camera, y toward net. All time-dependent quantities use `tsec(frame)` (`series.py`) or `T_of` (`ball.py`), never `frame/30` for the back view.
