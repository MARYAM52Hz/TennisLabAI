import numpy as np, json
W,H=928,1696
def cam_basis(cam,tg):
    cam=np.asarray(cam,float); tg=np.asarray(tg,float); f=tg-cam; f/=np.linalg.norm(f); r=np.cross(f,[0,0,1.0]); r/=np.linalg.norm(r); u=np.cross(r,f); return cam,f,r,u
def project(P,cam,tg,fov):
    c,f,r,u=cam_basis(cam,tg); P=np.atleast_2d(P)-c; z=P@f; fp=(W/2)/np.tan(np.radians(fov)/2)
    return np.c_[W/2+fp*(P@r)/z, H/2-fp*(P@u)/z], z
