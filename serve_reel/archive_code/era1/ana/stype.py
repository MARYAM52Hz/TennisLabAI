import pickle,numpy as np,sys
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/lab2'); sys.argv=['x']
import ball_lab as B
ba=pickle.load(open(SP+'/lab2/ball3d.pkl','rb'))
d=np.load(SP+'/lab2/player3d_lab.npz',allow_pickle=True); X=d['X']; nm=list(d['names']); I={k:i for i,k in enumerate(nm)}
print('player frames',X.shape)
for key in ('A','B2'):
    F=ba[key]; f0=F['f0']; tc=f0+F['tc']/B.DT
    fr=np.arange(f0,f0+90); P=B.positions(F,fr)
    pre=(fr<tc); k=np.argmax(np.where(pre,P[:,2],-9)); fa=fr[k]
    print(key,'contact frame %.2f'%tc,'apex frame',fa,'apex pos',P[k].round(2),'contact pos',B.positions(F,[tc])[0].round(2))
    hip=X[fa,[I['left_hip'],I['right_hip']]].mean(0); sh=X[fa,[I['left_shoulder'],I['right_shoulder']]].mean(0)
    print('  body at apex: hip',hip.round(2),'shoulder mid',sh.round(2),' toss rel shoulder (dx lateral, dy toward net) =',(P[k,:2]-sh[:2]).round(2))
    v1=F['v1']; sp=np.linalg.norm(v1); print('  v1',v1.round(1),'speed %.1f m/s = %.0f km/h'%(sp,sp*3.6),'launch angle %.1f deg'%np.degrees(np.arcsin(v1[2]/sp)),'lateral %.1f deg'%np.degrees(np.arctan2(v1[0],v1[1])))
    m=fr>=tc; yy=P[m,1]; zz=P[m,2]; z_net=np.interp(0,yy,zz)
    print('  height over net %.2f m (net 0.914 -> clearance %.2f m)'%(z_net,z_net-0.914))
    zb=np.where((fr>tc)&(P[:,2]<0.06))[0]
    if len(zb):
        ib=zb[0]; print('  bounce frame',fr[ib],'pos',P[ib].round(2)); vz=(P[ib,2]-P[ib-1,2])*30; vy=(P[ib,1]-P[ib-1,1])*30
        print('  incoming angle %.1f deg'%np.degrees(np.arctan2(-vz,vy)),' rebound z +1..4 frames',P[ib+1:ib+5,2].round(2))
print('--- incoming angle at bounce')
for key,fb in (('A',39),('B2',201)):
    F=ba[key]; P=B.positions(F,np.arange(fb-6,fb+1,0.5)); i=np.argmin(P[:,2]); 
    d=P[max(i-2,0)]-P[max(i-4,0)]; print(key,'descent angle before bounce %.1f deg'%np.degrees(np.arctan2(-(P[i-1,2]-P[i-3,2]),np.hypot(*(P[i-1,:2]-P[i-3,:2])))),'bounce at y=%.2f x=%.2f'%(P[i,1],P[i,0]))
