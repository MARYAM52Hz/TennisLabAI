import pickle, numpy as np, cv2
from scipy.optimize import least_squares
SP = __import__('os').environ['REEL_JOB']; JC = __import__('json').load(open(SP + '/job.json')); d=pickle.load(open(SP+'/nl/labels.pkl','rb')); court=d['court']
Y,S,X1,X2=11.885,6.40,4.115,5.485
WORLD={'far_baseline_singles_left':(-X1,Y),'far_baseline_doubles_left':(-X2,Y),'far_baseline_center_mark':(0,Y),'far_baseline_singles_right':(X1,Y),'far_baseline_doubles_right':(X2,Y),
 'far_service_singles_left':(-X1,S),'far_service_center_T':(0,S),'far_service_singles_right':(X1,S),
 'near_service_singles_left':(-X1,-S),'near_service_center_T':(0,-S),'near_service_singles_right':(X1,-S),
 'near_baseline_doubles_left':(-X2,-Y),'near_baseline_singles_left':(-X1,-Y),'near_baseline_center_mark':(0,-Y),'near_baseline_singles_right':(X1,-Y),'near_baseline_doubles_right':(X2,-Y)}
NET={'net_doubles_left':(-X2,0),'net_singles_left':(-X1,0),'net_singles_right':(X1,0),'net_doubles_right':(X2,0)}
cx0,cy0=JC['W']/2,JC['H']/2
def rotmat(psi,th,ph):
    f=np.array([np.cos(th)*np.sin(psi),np.cos(th)*np.cos(psi),-np.sin(th)]); r=np.cross(f,[0,0,1.0]); r/=np.linalg.norm(r); dn=np.cross(f,r); c,s=np.cos(ph),np.sin(ph); return np.stack([c*r+s*dn,-s*r+c*dn,f])
def project(p,X):
    f,psi,th,ph,Cx,Cy,Cz=p[:7]; R=rotmat(psi,th,ph); Xc=(np.atleast_2d(X)-[Cx,Cy,Cz])@R.T; return np.c_[f*Xc[:,0]/Xc[:,2]+cx0,f*Xc[:,1]/Xc[:,2]+cy0]
names=list(WORLD); Wp=np.array([[*WORLD[n],0.0] for n in names]); Up=np.array([court[n] for n in names])
def res(p,use=None):
    idx=range(len(names)) if use is None else use; r=(project(p,Wp[list(idx)])-Up[list(idx)]).ravel(); return r
if __name__=='__main__' and JC.get('camera_npz'):
    import shutil; shutil.copy(JC['camera_npz'],SP+'/nl/camera.npz'); print('camera taken from',JC['camera_npz'])
elif __name__=='__main__':
    best=None
    for f0 in (700,1000,1500,2200):
        for dist in (5,8,12,20):
            for z in (1.0,1.5,2.0):
                p0=[f0,0.0,0.05,0.0,0.0,-(dist+Y),z]
                try: s=least_squares(lambda p: np.r_[res(p),(p[6]-1.5)/3.0],p0,loss='soft_l1',f_scale=3.0)
                except Exception: continue
                if best is None or s.cost<best.cost: best=s
    use=list(range(len(names)))                       # outlier rejection: hand-clicked court points that are far off (e.g. near baseline outside the image) are dropped and the camera refitted
    for it in range(4):
        e_=np.linalg.norm(project(best.x,Wp[use])-Up[use],axis=1); keep=[u for u,v in zip(use,e_) if v<=max(20.0,2.5*float(np.median(e_)))]
        if len(keep)==len(use) or len(keep)<10: break
        use=keep; best=least_squares(lambda p: np.r_[res(p,use),(p[6]-1.5)/3.0],best.x,loss='soft_l1',f_scale=3.0)
    print('court points used: %d / %d'%(len(use),len(names)))
    p=best.x; print('f %.0f yaw %.2f pitch %.2f roll %.2f  C=(%.2f,%.2f,%.2f) cost %.1f'%(p[0],*np.degrees(p[1:4]),*p[4:7],best.cost))
    e=np.linalg.norm(project(p,Wp)-Up,axis=1)
    for n,v in zip(names,e): print('  %-30s %.1f px'%(n,v))
    for z in (0.0,0.914,1.07):
        for n,(x,y) in NET.items(): 
            uv=project(p,np.array([[x,y,z]]))[0]; print('net',n,'z',z,'proj',uv.round(0),'label',court[n],'err %.1f'%np.linalg.norm(uv-court[n]))
    med=float(np.median(e)); print('median court reprojection error %.1f px'%med); print('WARNING: poor court calibration (check the court labels)' if med>15 else 'calibration OK')
    # sensitivity to human error: leave-one-out and 4 px click noise (does the camera move if a point is clicked badly?)
    def _refit(U_,use_): return least_squares(lambda q: np.r_[(project(q,Wp[use_])-U_[use_]).ravel(),(q[6]-1.5)/3.0],p,loss='soft_l1',f_scale=3.0).x
    loo={}
    for u in use:
        q=_refit(Up,[v for v in use if v!=u]); loo[names[u]]=[float(q[0]-p[0]),float(np.linalg.norm(q[4:7]-p[4:7]))]
    rng=np.random.default_rng(0); nz=[_refit(Up+rng.normal(0,4.0,Up.shape),use) for _ in range(12)]
    sens=dict(loo_df_max=float(max(abs(v[0]) for v in loo.values())),loo_dcam_max=float(max(v[1] for v in loo.values())),most_influential=max(loo,key=lambda k:loo[k][1]),
              noise4px_f_std_pct=float(100*np.std([q[0] for q in nz])/p[0]),noise4px_cam_std_m=float(np.sqrt(np.sum(np.var([q[4:7] for q in nz],axis=0)))))
    print('sensitivity',sens)
    import json as _j
    _inl=[names[u] for u in use]; _rej=[n for n in names if n not in _inl]
    _j.dump(dict(f=float(p[0]),yaw=float(np.degrees(p[1])),pitch=float(np.degrees(p[2])),roll=float(np.degrees(p[3])),cam=[float(v) for v in p[4:7]],median_px=med,
        n_total=len(names),n_used=len(use),used=_inl,rejected=_rej,err_px={n:float(v) for n,v in zip(names,e)},
        net_err_px={'z%.3f'%z:float(np.mean([np.linalg.norm(project(p,np.array([[x,y,z]]))[0]-court[n]) for n,(x,y) in NET.items()])) for z in (0.0,0.914,1.07)},W=int(2*cx0),H=int(2*cy0),sensitivity=sens),open(SP+'/nl/calib_report.json','w'),indent=1)
    np.savez(SP+'/nl/camera.npz',K=np.array([[p[0],0,cx0],[0,p[0],cy0],[0,0,1.0]]),R=rotmat(*p[1:4]),cam=p[4:7],p=p)
