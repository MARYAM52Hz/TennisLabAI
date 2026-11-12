import pickle,numpy as np,sys
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/lab2'); sys.argv=['x']
import ball_lab as B
ba=pickle.load(open(SP+'/lab2/ball3d.pkl','rb'))
for key,tid,f0,f1,fb in (('A','175',0,77,39),('B2','0',148,213,201)):
    F=ba[key]; o=B.obs(tid,range(f0,f1)); P=B.positions(F,o[:,0]); uv,z=B.project(P); e=np.linalg.norm(uv-o[:,1:3],axis=1)
    post=o[:,0]>=fb
    print(key,'bounce frame',fb,'post-bounce frames',post.sum(),'reproj err post: mean %.1f max %.1f'%(e[post].mean(),e[post].max()),' pre mean %.1f'%e[~post].mean())
    print('  post-bounce fitted z (m):',[(int(o[i,0]),round(float(P[i,2]),2)) for i in np.where(post)[0][::2]])
    print('  post-bounce fitted y (m):',[(int(o[i,0]),round(float(P[i,1]),1)) for i in np.where(post)[0][::4]])
    print('  max z after bounce %.2f m'%P[post,2].max(),' (frame %d)'%o[post][P[post,2].argmax(),0])
    print('  obs v (px) post:',[(int(o[i,0]),round(o[i,2])) for i in np.where(post)[0][::3]])
