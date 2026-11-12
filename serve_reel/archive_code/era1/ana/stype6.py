import pickle,numpy as np,sys
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/lab2'); sys.argv=['x']
import ball_lab as B
ba=pickle.load(open(SP+'/lab2/ball3d.pkl','rb'))
d=np.load(SP+'/lab2/player3d_lab.npz',allow_pickle=True); X=d['X']; nm=list(d['names']); I={k:i for i,k in enumerate(nm)}
for key,fa_,fc in (('A',12,23),('B2',172,184)):
    F=ba[key]; tc=F['f0']+F['tc']/B.DT
    for lbl,f,tt in (('toss apex',fa_,fa_),('contact',fc,tc)):
        b=B.positions(F,[tt])[0]; rs=X[f,I['right_shoulder']]; ls=X[f,I['left_shoulder']]; ts=X[f,I['top_spine']]; hip=X[f,[I['left_hip'],I['right_hip']]].mean(0)
        print(key,lbl,'ball x %.2f | R-shoulder x %.2f L-shoulder x %.2f mid %.2f neck %.2f hip-mid %.2f'%(b[0],rs[0],ls[0],(rs[0]+ls[0])/2,ts[0],hip[0]),' -> ball minus R-shoulder %.2f, minus neck %.2f (neg = server\'s left)'%(b[0]-rs[0],b[0]-ts[0]))
