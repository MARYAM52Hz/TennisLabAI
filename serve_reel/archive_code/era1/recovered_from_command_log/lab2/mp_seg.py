import numpy as np, cv2, mediapipe as mp
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'
FR = np.load(SP + '/lab2/frames_ref.npy', mmap_mode='r'); cent = np.load(SP + '/lab2/cent.npy'); N = 237
pose = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1, enable_segmentation=True, min_detection_confidence=0.3)
side, SC = 380, 3.0; SEG = np.zeros((N, 848, 464), np.uint8)
for f in range(N):
    c = cent[f]; x0 = int(np.clip(c[0] - 120, 0, 464 - 240)); x1 = x0 + 240; y0 = int(np.clip(c[1] - side / 2, 0, 848 - side))
    crop = cv2.resize(np.array(FR[f][y0:y0 + side, x0:x1]), None, fx=SC, fy=SC, interpolation=cv2.INTER_CUBIC); r = pose.process(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)); seg = np.zeros((848, 464), np.float32)
    if r.segmentation_mask is not None: seg[y0:y0 + side, x0:x1] = cv2.resize(r.segmentation_mask, (x1 - x0, side), interpolation=cv2.INTER_AREA)
    SEG[f] = (np.clip(seg, 0, 1) * 255).astype(np.uint8)
    if f % 60 == 0: print('mp', f, flush=True)
np.save(SP + '/lab2/mp_seg.npy', SEG)
