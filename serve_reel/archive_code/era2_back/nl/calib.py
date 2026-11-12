import pickle, numpy as np, cv2
from scipy.optimize import least_squares
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; d=pickle.load(open(SP+'/nl/labels.pkl','rb')); court=d['court']
Y,S,X1,X2=11.885,6.40,4.115,5.485
WORLD={'far_baseline_singles_left':(-X1,Y),'far_baseline_doubles_left':(-X2,Y),'far_baseline_center_mark':(0,Y),'far_baseline_singles_right':(X1,Y),'far_baseline_doubles_right':(X2,Y),
 'far_service_singles_left':(-X1,S),'far_service_center_T':(0,S),'far_service_singles_right':(X1,S),
 'near_service_singles_left':(-X1,-S),'near_service_center_T':(0,-S),'near_service_singles_right':(X1,-S),
 'near_baseline_doubles_left':(-X2,-Y),'near_baseline_singles_left':(-X1,-Y),'near_baseline_center_mark':(0,-Y),'near_baseline_singles_right':(X1,-Y),'near_baseline_doubles_right':(X2,-Y)}
NET={'net_doubles_left':(-X2,0),'net_singles_left':(-X1,0),'net_singles_right':(X1,0),'net_doubles_right':(X2,0)}
cx0,cy0=360.0,640.0
def rotmat(psi,th,ph):
    f=np.array([np.cos(th)*np.sin(psi),np.cos(th)*np.cos(psi),-np.sin(th)]); r=np.cross(f,[0,0,1.0]); r/=np.linalg.norm(r); dn=np.cross(f,r); c,s=np.cos(ph),np.sin(ph); return np.stack([c*r+s*dn,-s*r+c*dn,f])
def project(p,X):
    f,psi,th,ph,Cx,Cy,Cz=p[:7]; R=rotmat(psi,th,ph); Xc=(np.atleast_2d(X)-[Cx,Cy,Cz])@R.T; return np.c_[f*Xc[:,0]/Xc[:,2]+cx0,f*Xc[:,1]/Xc[:,2]+cy0]
names=list(WORLD); Wp=np.array([[*WORLD[n],0.0] for n in names]); Up=np.array([court[n] for n in names])
def res(p,use=None):
    idx=range(len(names)) if use is None else use; r=(project(p,Wp[list(idx)])-Up[list(idx)]).ravel(); return r
if __name__=='__main__':
    best=None
    for f0 in (700,1000,1500,2200):
        for dist in (5,8,12,20):
            for z in (1.0,1.5,2.0):
                p0=[f0,0.0,0.05,0.0,0.0,-(dist+Y),z]
                try: s=least_squares(lambda p: np.r_[res(p),(p[6]-1.5)/3.0],p0,loss='soft_l1',f_scale=3.0)
                except Exception: continue
                if best is None or s.cost<best.cost: best=s
    p=best.x; print('f %.0f yaw %.2f pitch %.2f roll %.2f  C=(%.2f,%.2f,%.2f) cost %.1f'%(p[0],*np.degrees(p[1:4]),*p[4:7],best.cost))
    e=np.linalg.norm(project(p,Wp)-Up,axis=1)
    for n,v in zip(names,e): print('  %-30s %.1f px'%(n,v))
    for z in (0.0,0.914,1.07):
        for n,(x,y) in NET.items(): 
            uv=project(p,np.array([[x,y,z]]))[0]; print('net',n,'z',z,'proj',uv.round(0),'label',court[n],'err %.1f'%np.linalg.norm(uv-court[n]))
    np.savez(SP+'/nl/camera.npz',K=np.array([[p[0],0,cx0],[0,p[0],cy0],[0,0,1.0]]),R=rotmat(*p[1:4]),cam=p[4:7],p=p)
