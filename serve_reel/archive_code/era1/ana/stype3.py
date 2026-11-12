import pickle,numpy as np,sys
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/lab2'); sys.argv=['x']
import ball_lab as B, jax.numpy as jnp
lab=pickle.load(open(SP+'/lab2/labels_ref.pkl','rb')); r=lab['racket']; print(type(r), (list(r.keys())[:12] if isinstance(r,dict) else np.shape(r)))
k=list(r.keys())[0]; print(k, np.shape(r[k]) if hasattr(r[k],'__len__') else r[k])
ba=pickle.load(open(SP+'/lab2/ball3d.pkl','rb'))
# e_v sensitivity post bounce
for key,tid,f0,f1,fb in (('A','175',0,77,39),('B2','0',148,213,201)):
    F=ba[key]; o=B.obs(tid,range(f0,f1)); post=o[:,0]>=fb; out=[]
    for ev in (0.55,0.65,0.74,0.85,0.95,1.05):
        P=np.asarray(B._sim(jnp.array(F['p0']),jnp.array(F['v0']),float(F['tc']),jnp.array(F['v1']),e_v=ev)); k_=(o[:,0]-F['f0'])*B.SUB; Pp=P[k_.astype(int)]
        uv,z=B.project(Pp); e=np.linalg.norm(uv-o[:,1:3],axis=1); out.append((ev,round(float(e[post].mean()),1),round(float(Pp[post,2].max()),2)))
    print(key,'e_v -> (post-bounce px err, max z after bounce):',out)
