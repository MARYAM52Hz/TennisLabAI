import pickle, numpy as np, sys
from scipy.optimize import least_squares
d=pickle.load(open('labels.pkl','rb')); court=d['court']
Y,S,X1,X2=11.885,6.40,4.115,5.485; cx0,cy0=360.0,640.0
WORLD={'far_baseline_singles_left':(-X1,Y),'far_baseline_doubles_left':(-X2,Y),'far_baseline_center_mark':(0,Y),'far_baseline_singles_right':(X1,Y),'far_baseline_doubles_right':(X2,Y),
 'far_service_singles_left':(-X1,S),'far_service_center_T':(0,S),'far_service_singles_right':(X1,S),
 'near_service_singles_left':(-X1,-S),'near_service_center_T':(0,-S),'near_service_singles_right':(X1,-S),
 'near_baseline_doubles_left':(-X2,-Y),'near_baseline_singles_left':(-X1,-Y),'near_baseline_center_mark':(0,-Y),'near_baseline_singles_right':(X1,-Y),'near_baseline_doubles_right':(X2,-Y)}
# world x along the baseline (x grows toward the camera in the image), y toward the net
def rotmat(psi,th,ph):
    f=np.array([np.cos(th)*np.sin(psi),np.cos(th)*np.cos(psi),-np.sin(th)]); r=np.cross(f,[0,0,1.0]); r/=np.linalg.norm(r); dn=np.cross(f,r); c,s=np.cos(ph),np.sin(ph); return np.stack([c*r+s*dn,-s*r+c*dn,f])
def project(p,X):
    f,psi,th,ph,Cx,Cy,Cz=p[:7]; R=rotmat(psi,th,ph); Xc=(np.atleast_2d(X)-[Cx,Cy,Cz])@R.T; return np.c_[f*Xc[:,0]/Xc[:,2]+cx0,f*Xc[:,1]/Xc[:,2]+cy0]
def fit(names,fixed_f=None,w=None):
    Wp=np.array([[*WORLD[n],0.0] for n in names]); Up=np.array([court[n] for n in names]); w=np.ones(len(names)) if w is None else np.array(w)
    def res(p):
        p=np.array(p); 
        if fixed_f: p[0]=fixed_f
        return np.r_[((project(p,Wp)-Up)*w[:,None]).ravel(),(p[6]-1.5)/3.0]
    best=None
    for f0 in (500,800,1200,2000,3500):
        for yaw in (-1.7,-1.5,-1.3):
            for Cx in (6,12,20):
                for Cy in (-14,-10,-6):
                    for th in (0.05,0.2):
                        p0=[f0,yaw,th,0.0,Cx,Cy,1.5]
                        try: s=least_squares(res,p0,loss='soft_l1',f_scale=3.0)
                        except Exception: continue
                        if best is None or s.cost<best.cost: best=s
    p=best.x.copy()
    if fixed_f: p[0]=fixed_f
    return p,best.cost,Wp,Up
if __name__=='__main__':
    sets={'inframe':[n for n in WORLD if 'near' in n],'all':list(WORLD)}
    for k,names in sets.items():
        p,c,Wp,Up=fit(names)
        print(k,'cost %.1f f %.0f yaw %.1f pitch %.1f roll %.2f C=(%.2f,%.2f,%.2f)'%(c,p[0],*np.degrees(p[1:4]),*p[4:7]))
        e=np.linalg.norm(project(p,Wp)-Up,axis=1); print('  rms %.1f px; per point'%np.sqrt((e**2).mean()),dict(zip([n[:12]+n[-5:] for n in names],e.round(1))))
        if k=='inframe':
            far=[n for n in WORLD if 'far' in n]; Wf=np.array([[*WORLD[n],0.0] for n in far]); Uf=np.array([court[n] for n in far]); print('  far pts pred-vs-label',np.linalg.norm(project(p,Wf)-Uf,axis=1).round(0))
        np.save('p_%s.npy'%k,p)
