import cv2, numpy as np, os, sys
sys.path.insert(0, '/tmp/claude-0/-home-claude/c5f26e6b-ec2e-54ad-a30c-648653015475/scratchpad/auto')
import glass; SP = glass.SP; plate = cv2.imread(SP + '/lay/plate.png'); n = 0
for k, f in enumerate(range(140, 223)):
    rb = cv2.imread(SP + f'/lay/rb{f:04d}.png', cv2.IMREAD_UNCHANGED); o = glass.glass_frame(f, plate, rb); cv2.imwrite(SP + f'/gl_enc/g{k:04d}.png', (o * 255).astype(np.uint8))
for j in range(83, 93): os.system(f'cp {SP}/gl_enc/g0082.png {SP}/gl_enc/g{j:04d}.png')
print('ok')
