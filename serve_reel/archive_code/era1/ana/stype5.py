import sys,numpy as np,pickle
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
for p in ('/lab2','/ana','/lab3'): sys.path.insert(0,SP+p)
from motion_lab2 import Motion2
M=Motion2()
for nm,tc in (('A',23.26),('B',183.79)):
    print(nm)
    for t in (tc-2,tc-1,tc-0.5,tc,tc+0.5):
        h=M.head_at(t); e=1/60.; v=(M.head_at(t+e)-M.head_at(t-e))/(2*e)
        b,R,_=M.racket(t); n=R[:,2] if False else None
        sp=np.linalg.norm(v); hv=np.hypot(v[0],v[1])
        print(' t %.2f head z %.2f v=(%.1f,%.1f,%.1f) |v|=%.1f m/s path elev %.0f deg lateral(x) share %.0f%%'%(t,h[2],*v,sp,np.degrees(np.arctan2(v[2],hv)),100*abs(v[0])/sp))
