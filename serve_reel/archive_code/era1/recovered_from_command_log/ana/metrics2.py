import sys, numpy as np, pickle
SP = '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad'; sys.path.insert(0, SP + '/lab2')
from motion_lab2 import Motion2
from scipy.ndimage import gaussian_filter1d
M = Motion2(); J = M.jf
def wrap(a): return (a + 180) % 360 - 180
def yawl(a, b): d = b - a; return np.degrees(np.arctan2(d[1], d[0]))
for key, lo, hi in (('A', 0, 40), ('B', 150, 200)):
    tc = M.tcs[key]; fr = np.arange(lo, hi + 1)
    hy = np.array([yawl(J('left_hip', f), J('right_hip', f)) for f in fr]); sy = np.array([yawl(J('left_shoulder', f), J('right_shoulder', f)) for f in fr])
    sep = wrap(sy - hy)
    hyu = np.degrees(np.unwrap(np.radians(hy))); syu = np.degrees(np.unwrap(np.radians(sy)))
    print(key, 'tc', tc)
    for f, a, b, s in zip(fr, hyu, syu, sep):
        if (f - lo) % 2 == 0: print(f, round(a), round(b), round(s))
