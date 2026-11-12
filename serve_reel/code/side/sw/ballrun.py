import sys, os, pickle, numpy as np
SP = __import__('os').environ['REEL_JOB']; JC = __import__('json').load(open(SP + '/job.json')); sys.path.insert(0,SP+'/sw')
import ball as BL
from ball import *
MODE=sys.argv[1] if len(sys.argv)>1 else 'free'
d=np.load(SP+'/sw/player3d_%s.npz'%MODE,allow_pickle=True); X=d['X']; nm=list(d['names']); I={k:i for i,k in enumerate(nm)}
F0,TC0=JC['f0'],JC['tc0']; lw=X[F0,I['left_wrist']]; el,rw_=X[TC0,I['right_elbow']],X[TC0,I['right_wrist']]; dirn=(rw_-el)/np.linalg.norm(rw_-el); tgt=rw_+0.45*dirn
print('left wrist@f0',lw.round(2),'contact target',tgt.round(2))
oS=obs(range(F0,JC['ball1']+1)); gp=None
tcp=(float(T_of(float(TC0))-T_of(F0)+0.002),0.006)
F=fit(oS,F0,float(TC0),tcp=tcp,nstart=int(os.environ.get('NS','40')),cpri=(tgt,np.array([0.35,0.5,0.5])),vprior=None,v1x=(0.0,4.0),rw=0.03,
      ypri=[(F0,lw[0],0.25),(TC0,tgt[0],0.35)])
P=positions(F,oS[:,0]); uv,z=project(P); e=np.linalg.norm(uv-oS[:,1:3],axis=1)
print('DTR %.5f reproj px: mean %.2f max %.2f at k %d'%(DTR,e.mean(),e.max(),oS[e.argmax(),0]),' max height %.2f'%P[:,2].max(),' tc k %.2f'%frame_of(T_of(F['f0'])+F['tc']),'speed %.1f m/s = %.0f km/h'%(np.linalg.norm(F['v1']),3.6*np.linalg.norm(F['v1'])))
print('cost',F['cost'],'v1',F['v1'].round(1),'p0',F['p0'].round(2))
if os.environ.get('SAVE'): pickle.dump({'S':F},open(SP+'/sw/ball3d.pkl','wb'))
