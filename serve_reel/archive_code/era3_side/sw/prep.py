"""IMG_7122 side view: unique frames S (every ~3rd container frame carries new content; 30 fps real capture, slow-motion export) -> lab2.pkl; camera (no court labels): f=659, level, distance from the player's height."""
import pickle, numpy as np
d=pickle.load(open('labels.pkl','rb')); S=np.load('S.npy'); T=len(S)
L=dict(skel={n:v[S] for n,v in d['skel'].items()},rack={n:v[S] for n,v in d['rack'].items()},
       face={k:d['face'][int(S[k])] for k in range(T) if int(S[k]) in d['face']},
       ball={k:d['ball'][int(S[k])] for k in range(T) if int(S[k]) in d['ball'] and not d['ball'][int(S[k])][4]},contacts=d['contacts'])
pickle.dump(L,open('lab2.pkl','wb')); print('unique frames',T,'ball labels',len(L['ball']))
# camera
f=659.0; cx,cy=360.0,640.0; sk=L['skel']
heel=(sk['left_heel'][0]+sk['right_heel'][0])/2; toe=(sk['left_foot_index'][0]+sk['right_foot_index'][0])/2; neck=sk['top_spine'][0]
vfoot=(heel[1]+toe[1])/2*0.6+heel[1]*0.4
H=1.80; neckz=0.818*H; ppm=(vfoot-neck[1])/neckz; D=f/ppm; Cz=D*(vfoot-cy)/f
print('foot v %.0f neck v %.0f -> %.0f px/m, D=%.2f m, camera height %.2f m'%(vfoot,neck[1],ppm,D,Cz))
def rotmat(psi,th,ph):
    fv=np.array([np.cos(th)*np.sin(psi),np.cos(th)*np.cos(psi),-np.sin(th)]); r=np.cross(fv,[0,0,1.0]); r/=np.linalg.norm(r); dn=np.cross(fv,r); c,s=np.cos(ph),np.sin(ph); return np.stack([c*r+s*dn,-s*r+c*dn,fv])
R=rotmat(-np.pi/2,0.0,0.0); C=np.array([D,0.0,Cz])
np.savez('camera.npz',K=np.array([[f,0,cx],[0,f,cy],[0,0,1.0]]),R=R,cam=C)
print(R.round(3)); 
