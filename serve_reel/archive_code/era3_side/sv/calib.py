"""Side-view camera (IMG_7122): only the near baseline is visible. World: x along the baseline (+x toward the camera), y toward the net, z up, baseline y=-11.885.
Constraints: baseline points (singles_left, centre, singles_right (+ doubles_left, low weight)), player stands upright at frame 0 (heels on ground, neck 1.47 m), roll~0, f prior 659."""
import pickle, numpy as np, sys
from scipy.optimize import least_squares
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; d=pickle.load(open(SP+'/sv/labels.pkl','rb')); court=d['court']; sk=d['skel']
Y,X1,X2=11.885,4.115,5.485; cx0,cy0=360.0,640.0
PTS={'near_baseline_singles_left':(-X1,-Y,4.0),'near_baseline_center_mark':(0,-Y,4.0),'near_baseline_singles_right':(X1,-Y,6.0),'near_baseline_doubles_left':(-X2,-Y,12.0)}
def rotmat(psi,th,ph):
    f=np.array([np.cos(th)*np.sin(psi),np.cos(th)*np.cos(psi),-np.sin(th)]); r=np.cross(f,[0,0,1.0]); r/=np.linalg.norm(r); dn=np.cross(f,r); c,s=np.cos(ph),np.sin(ph); return np.stack([c*r+s*dn,-s*r+c*dn,f])
def project(p,X):
    f,psi,th,ph,Cx,Cy,Cz=p[:7]; R=rotmat(psi,th,ph); Xc=(np.atleast_2d(X)-[Cx,Cy,Cz])@R.T; return np.c_[f*Xc[:,0]/Xc[:,2]+cx0,f*Xc[:,1]/Xc[:,2]+cy0]
heel=(sk['left_heel'][0]+sk['right_heel'][0])/2; neck=sk['top_spine'][0]; NECKZ=float(sys.argv[1]) if len(sys.argv)>1 else 1.47
def res(p,fixf=None):
    p=np.array(p); 
    if fixf: p[0]=fixf
    r=[]
    for n,(x,y,s) in PTS.items(): r+=list((project(p,[[x,y,0.0]])[0]-court[n])/s)
    xp,yp=p[7:9]; r+=list((project(p,[[xp,yp,0.0]])[0]-heel)/10.0); r+=list((project(p,[[xp,yp,NECKZ]])[0]-neck)/15.0)
    r+=[np.degrees(p[3])/2.0,0.0]; return np.array(r)
if __name__=='__main__':
    best=None; fixf=float(sys.argv[2]) if len(sys.argv)>2 else None
    for Cx in (8,15,25):
        for Cy in (-14,-11,-8):
            for Cz in (1.0,2.0,3.0):
                for th in (3,10,20):
                    p0=[3000,-np.pi/2,np.radians(th),0.0,Cx,Cy,Cz,0.0,-11.9]
                    try: s=least_squares(res,p0,args=(fixf,),loss='soft_l1',f_scale=2.0)
                    except Exception: continue
                    if best is None or s.cost<best.cost: best=s
    p=best.x.copy()
    if fixf: p[0]=fixf
    print('cost %.2f f %.0f yaw %.1f pitch %.1f roll %.2f C=(%.2f,%.2f,%.2f) player=(%.2f,%.2f)'%(best.cost,p[0],*np.degrees(p[1:4]),*p[4:9]))
    for n,(x,y,s) in PTS.items(): print('  %-28s err %.1f px'%(n,np.linalg.norm(project(p,[[x,y,0]])[0]-court[n])))
    print('  heel err %.1f neck err %.1f'%(np.linalg.norm(project(p,[[p[7],p[8],0]])[0]-heel),np.linalg.norm(project(p,[[p[7],p[8],NECKZ]])[0]-neck)))
    if len(sys.argv)<=3: np.savez(SP+'/sv/camera.npz',K=np.array([[p[0],0,cx0],[0,p[0],cy0],[0,0,1.0]]),R=rotmat(*p[1:4]),cam=p[4:7],p=p)
