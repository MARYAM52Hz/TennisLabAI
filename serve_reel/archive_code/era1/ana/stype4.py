import pickle,numpy as np
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'
lab=pickle.load(open(SP+'/lab2/labels_ref.pkl','rb')); r=lab['racket']
for nm,tc in (('A',23.26),('B',183.79)):
    print(nm)
    fs=range(int(tc)-6,int(tc)+4)
    prev=None
    for f in fs:
        fc=r[f]['face']; c=fc['c']; a,b=fc['axes']; ang=fc['ang']
        v=(c-prev) if prev is not None else np.zeros(2); prev=c
        print(f,'c',c.round(0),'axes %.1f/%.1f ratio %.2f'%(max(a,b),min(a,b),min(a,b)/max(a,b)),'ang %.0f'%ang,'v(px/f) dx %.1f dy %.1f'%tuple(v),'out',fc['outside'])
