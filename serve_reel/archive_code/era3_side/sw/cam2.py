"""Side-view camera for IMG_7122 WITHOUT the (unreliable) court labels.
Assumptions: f=F (phone main lens, same phone as IMG_7125 -> 659 px), roll=pitch=0 (verticals/slats are vertical/horizontal in the image),
player 1.80 m, upright at frame 0 (neck 0.82 H) with heels on the ground. The visible white baseline gives the world axes."""
import numpy as np, pickle, sys
F=float(sys.argv[1]) if len(sys.argv)>1 else 659.0; H=1.80; cx0,cy0=360.0,640.0; XP=2.0; YB=-11.885
d=pickle.load(open('labels.pkl','rb')); sk=d['skel']
heel_v=np.mean([sk['left_heel'][0][1],sk['right_heel'][0][1]]); neck_v=sk['top_spine'][0][1]
Cz=0.82*H*(heel_v-cy0)/(heel_v-neck_v)          # camera height from the neck/heel pixel ratio
def ground(u,v): dd=F*Cz/(v-cy0); return np.array([(u-cx0)*dd/F,dd])        # (a,d) on the ground
bl=np.array([d['court'][k] for k in ('near_baseline_singles_left','near_baseline_center_mark','near_baseline_singles_right','near_baseline_doubles_right')])
G=np.array([ground(*p) for p in bl]); c=G.mean(0); u_,s_,vt=np.linalg.svd(G-c); e=vt[0]; e=e if e[1]>0 else -e   # direction away from the camera
res=np.linalg.norm((G-c)-np.outer((G-c)@e,e),axis=1); print('line fit residual (m)',res.round(3),' angle to optical axis %.1f deg'%np.degrees(np.arctan2(e[0],e[1])))
xd=np.array([-e[0],-e[1],0.0]); zd=np.array([0,0,1.0]); yd=np.cross(zd,xd)
Df=F*(0.82*H)/(heel_v-neck_v); gf=ground(*np.mean([sk['left_heel'][0],sk['right_heel'][0]],axis=0))   # player's foot point (a,d)
# point on the baseline at the player's depth: line point with d=gf[1]
t=(gf[1]-c[1])/e[1]; P0=c+t*e
print('camera height %.2f m, player depth %.2f m (neck-based %.2f)'%(Cz,gf[1],Df),' foot a=%.2f  line a=%.2f -> behind baseline by %.2f m'%(gf[0],P0[0],(gf[0]-P0[0])*np.dot([1,0],yd[:2])*-1))
def to_w(a,dd,h): p=np.array([a,dd,0.0])-np.array([P0[0],P0[1],0.0]); return np.array([p@xd+XP,p@yd+YB,h])
Cw=np.array([ (np.array([0,0])-P0)@xd[:2]+XP, (np.array([0,0])-P0)@yd[:2]+YB, Cz])
right=np.array([1.0,0,0,]); fwd=np.array([0,1.0,0]); down=np.array([0,0,-1.0])
Rm=np.array([[right@xd,right@yd,0],[0,0,-1.0],[fwd@xd,fwd@yd,0]])
K=np.array([[F,0,cx0],[0,F,cy0],[0,0,1.0]]); print('C world',Cw.round(3)); print('R',Rm.round(3))
foot_w=to_w(*gf,0.0); print('player foot world',foot_w.round(2))
def proj(X): Xc=(np.atleast_2d(X)-Cw)@Rm.T; return np.c_[F*Xc[:,0]/Xc[:,2]+cx0,F*Xc[:,1]/Xc[:,2]+cy0]
print('baseline pts reproj err',[np.linalg.norm(proj([[ *( (to_w(*g,0)[:2]) ),0.0]])[0]-p).round(1) for g,p in zip(G,bl)])
print('neck reproj', proj([[foot_w[0],foot_w[1],0.82*H]])[0].round(1), 'label',sk['top_spine'][0].round(1))
np.savez('camera.npz',K=K,R=Rm,cam=Cw,p=np.array([F,0,0,0,*Cw,foot_w[0],foot_w[1]]))
