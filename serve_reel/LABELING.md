# CVAT labelling guide (what the kit reads)

Export: Task → Actions → Export task dataset → **"CVAT for video 1.1"** (zip). Use the same label set as the example exports in `examples/` (import one of them as a template, or ask the owner of the CVAT project to share it).

| label | type | where | used for |
|---|---|---|---|
| `P_player_skeleton` | skeleton, 18 points: left/right shoulder, elbow, wrist, hip, knee, ankle, heel, foot_index, top_spine (neck base), bottom_spine (pelvis centre) | every frame of the serve | the 3D body |
| `R_racket_skeleton` | skeleton (string_bed_center needed) | every frame | racket |
| `R_racket_face` | ellipse around the string bed | every frame | racket orientation |
| `B_ball` | ellipse | from the toss (ball in the hand) until the end of the clip; several `B_ball` tracks are allowed — the one at the contact point is used | ball path |
| `B_contact_racket` | point | **exactly one**, on the contact frame, on the ball | contact instant |
| `B_contact_ground` | point | back view: the bounce of the serve (after contact) | ball-fit anchor |
| `C_structured_court` | skeleton, 16 line-intersection points (far/near baseline, service line, T, centre mark…) | back view only, frame 0 | camera calibration |

Tips: label every frame of the video (CVAT interpolation is fine, then correct the key frames); the clip should contain the whole serve — from at least 1 s before the toss to ~0.6 s after contact — with the player fully visible. Side view: slow-motion exports with repeated frames are handled automatically; the contact label may be on any repeated copy of the contact picture.
Not needed: `M_player_info`, `E_serve_stage` tags, `B_ball_center`, side-view court labels.

See also INPUT_STANDARDS_AND_CALIBRATION.md §2 (accuracy targets, keyframe spacing, occluded vs outside, the common human mistakes and which QC check catches each one).
