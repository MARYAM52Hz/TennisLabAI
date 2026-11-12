"""Side-view camera without a usable court: phone f (659 from IMG_7125), baseline LINE direction only, player upright at frame 0 (height H), soft pitch/roll/height priors."""
import pickle, numpy as np, sys
from scipy.optimize import least_squares
d=pickle.load(open('labels.pkl','rb')); court=d['court']; sk=d['skel']
Y=11.885; cx0,cy0=360.0,640.0
LINE=[court[n] for n in ('near_baseline_singles_left','near_baseline_center_mark','near_baseline_singles_right','near_baseline_doubles_right')]
def rotmat(psi,th,ph):
    f=np.array([np.cos(th)*np.sin(psi),np.cos(th)*np.cos(psi),-np.sin(th)]); r=np.cross(f,[0,0,1.0]); r/=np.linalg.norm(r); dn=np.cross(f,r); c,s=np.cos(ph),np.sin(ph); return np.stack([c*r+s*dn,-s*r+c*dn,f])
def project(p,X,f):
    psi,th,ph,Cx,Cy,Cz=p[:6]; R=rotmat(psi,th,ph); Xc=(np.atleast_2d(X)-[Cx,Cy,Cz])@R.T; return np.c_[f*Xc[:,0]/Xc[:,2]+cx0,f*Xc[:,1]/Xc[:,2]+cy0]
heel=(sk['left_heel'][0]+sk['right_heel'][0])/2; neck=sk['top_spine'][0]; pel=sk['bottom_spine'][0]
def res(p,f,H):
    r=[]
    a=project(p,[[-8,-Y,0]],f)[0]; b=project(p,[[8,-Y,0]],f)[0]; t=(b-a)/np.linalg.norm(b-a); nrm=np.array([-t[1],t[0]])
    for q in LINE: r.append(np.dot(q-a,nrm)/3.0)
    xp,yp=p[6:8]
    r+=list((project(p,[[xp,yp,0.0]],f)[0]-heel)/10.0); r+=list((project(p,[[xp,yp,0.818*H]],f)[0]-neck)/15.0); r+=list((project(p,[[xp,yp,0.53*H]],f)[0]-pel)/25.0)
    r+=[np.degrees(p[2])/1.5, np.degrees(p[1])/6.0, (yp+12.4)/0.6]          # roll~0, pitch~0 (+-6), player ~0.5 m behind the baseline
    return np.array(r)
def solve(f=659.0,H=1.80,verbose=True):
    best=None
    for Cx in (4,8,14):
        for Cy in (-14,-12,-10):
            for Cz in (0.8,1.3,2.0):
                for th in (-0.05,0.05):
                    p0=[-np.pi/2,th,0.0,Cx,Cy,Cz,0.5,-12.4]
                    try: s=least_squares(res,p0,args=(f,H),loss='soft_l1',f_scale=2.0)
                    except Exception: continue
                    if best is None or s.cost<best.cost: best=s
    p=best.x
    if verbose:
        print('f %.0f H %.2f cost %.2f yaw %.1f pitch %.1f roll %.2f  C=(%.2f,%.2f,%.2f) player=(%.2f,%.2f)  m/px at player %.4f'%(f,H,best.cost,*np.degrees(p[:3]),*p[3:8],H/ (project(p,[[p[6],p[7],0]],f)[0][1]-project(p,[[p[6],p[7],H]],f)[0][1])))
    return p,best
if __name__=='__main__':
    for f in (550,659,800,1000):
        p,b=solve(f)
    p,b=solve(659.0)
    r=res(p,659.0,1.8); print('residuals',np.round(r,2))
    np.save('p3.npy',p)
