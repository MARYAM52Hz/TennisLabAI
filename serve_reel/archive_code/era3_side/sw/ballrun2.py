import sys, os, pickle, numpy as np
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/sw')
import ball as BL
from ball import *
MODE=sys.argv[1] if len(sys.argv)>1 else 'free'
d=np.load(SP+'/sw/player3d_%s.npz'%MODE,allow_pickle=True); X=d['X']; nm=list(d['names']); I={k:i for i,k in enumerate(nm)}
lw=X[5,I['left_wrist']]; print('left wrist@5',lw.round(2))
XR=float(os.environ.get('XR','2.59'))
oS=obs(range(5,34)); tcp=(float(T_of(32.0)-T_of(5)),0.004)
F=fit(oS,5,32.0,tcp=tcp,nstart=int(os.environ.get('NS','60')),cpri=(np.array([XR,-11.5,2.7]),np.array([0.12,9.0,9.0])),vprior=(36,14),rw=float(os.environ.get('RW','0.1')),
      ypri=[(5,lw[0],0.3)],latp=0.12,netp=(1.35,0.4),landp=(5.0,1.3))
P=positions(F,oS[:,0]); uv,z=project(P); e=np.linalg.norm(uv-oS[:,1:3],axis=1)
print("v1",F["v1"].round(2),"tc",F["tc"]); sys.stdout.flush()
print('reproj px: mean %.2f max %.2f at k %d'%(e.mean(),e.max(),oS[e.argmax(),0]),' max height %.2f'%P[:,2].max(),' tc k %.2f'%frame_of(T_of(F['f0'])+F['tc']),'speed %.1f m/s = %.0f km/h'%(np.linalg.norm(F['v1']),3.6*np.linalg.norm(F['v1'])))
T=np.arange(0,3.0,0.01); Q=sim(F['p0'],F['v0'],F['tc'],F['v1'],T); post=T>=F['tc']; iy=np.where(post&(Q[:,1]>0))[0][0]; il=np.where(post&(Q[:,2]<=RB+1e-6))[0]
print('v1',F['v1'].round(2),'angle lateral %.1f deg launch %.1f deg'%(np.degrees(np.arctan2(F['v1'][0],F['v1'][1])),np.degrees(np.arctan2(F['v1'][2],np.hypot(F['v1'][0],F['v1'][1])))),'net clearance z=%.2f'%Q[iy,2],'land',Q[il[0]][:2].round(2) if len(il) else None,'p0',F['p0'].round(2),'contact pos',positions(F,[31.999])[0].round(2))
if os.environ.get('SAVE'): pickle.dump({'S':F},open(SP+'/sw/ball3d.pkl','wb')); print('saved')
