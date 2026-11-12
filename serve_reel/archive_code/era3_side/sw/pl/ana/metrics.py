import sys, numpy as np, pickle, json
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/sw/pl'); sys.path.insert(0,SP+'/sw/pl/ana'); sys.path.insert(0,SP+'/sw')
from series import build, ang, nrm, tsec
from scipy.signal import savgol_filter
import ball as BL
M,S=build(); lab=pickle.load(open(SP+'/sw/labels2.pkl','rb')); bl=pickle.load(open(SP+'/sw/ball3d.pkl','rb'))['S']
sm={k:savgol_filter(v,5,2) for k,v in S.items()}; BASE=-11.885
at=lambda k,f: float(np.interp(f,np.arange(M.T),sm[k])); J=lambda n,f: M.jf(n,f); tc=M.tc
w=np.arange(10,29); kn=(sm['kneeL']+sm['kneeR'])/2; tr=int(w[np.argmax(kn[w])])
wl=np.arange(tr+2,int(tc)-1); lo=int(wl[np.argmin(sm['rackZ'][wl])])
zL=np.array([J('left_ankle',f)[2] for f in range(M.T)]); land=[f for f in range(int(tc)+1,M.T) if zL[f]<0.14]; fl=land[0] if land else int(tc)+6
p2=lambda n,f: np.array(lab['skel'][n][f],float)
def elbow2d(f): return 180-ang(np.r_[p2('right_shoulder',f),0],np.r_[p2('right_elbow',f),0],np.r_[p2('right_wrist',f),0])
d=dict(events=dict(trophy=tr,low=lo,contact=round(tc,2),landing=fl))
d['times_ms']=dict(trophy_to_contact=round((tsec(tc)-tsec(tr))*1000),low_to_contact=round((tsec(tc)-tsec(lo))*1000))
d['trophy']=dict(kneeFront=at('kneeL',tr),kneeBack=at('kneeR',tr),trunkInc=at('trunkInc',tr),shTilt=at('shTilt',tr))
d['low']=dict(elbow2D=float(elbow2d(lo)),elbow3D=at('elbowR',lo),rackZ=at('rackZ',lo))
b=M.ball(tc); neck=J('top_spine',tc)
d['contact']=dict(ballXYZ=b.round(3).tolist(),height=float(b[2]),ahead=float(b[1]-BASE),elbow2D=float(elbow2d(int(round(tc)))),elbow3D=at('elbowR',tc),shTilt=at('shTilt',tc),trunkInc=at('trunkInc',tc),ball_minus_neck_y=float(b[1]-neck[1]),pelvisZ=at('pelvisZ',tc))
ts=np.linspace(bl['f0']+2,tc,800); zs=np.array([M.ball(t)[2] for t in ts]); i=int(np.argmax(zs)); pb=M.ball(ts[i]); neck_a=J('top_spine',ts[i])
d['toss']=dict(apexFrame=float(ts[i]),apexZ=float(zs[i]),apex_minus_neck_y=float(pb[1]-neck_a[1]),apex_minus_head_y=float(pb[1]-J('head',ts[i])[1]),apex_to_contact_ms=float((tsec(tc)-tsec(ts[i]))*1000),apex_ahead_baseline=float(pb[1]-BASE),release_z=float(M.ball(bl['f0'])[2]))
v1=bl['v1']; sp=float(np.linalg.norm(v1)); fr=np.arange(tc,62.0,0.1); P=BL.positions(bl,fr)
z_net=float(np.interp(0,P[:,1],P[:,2])) if P[:,1].max()>0 else float('nan'); ib=int(np.argmax(P[:,2]<0.06)) if (P[:,2]<0.06).any() else -1
d['ball']=dict(speed_ms=sp,speed_kmh=sp*3.6,launch_deg=float(np.degrees(np.arcsin(v1[2]/sp))),lateral_deg=float(np.degrees(np.arctan2(v1[0],v1[1]))),net_clear=z_net-0.914,bounce_xy=(P[ib,:2].round(2).tolist() if ib>=0 else None))
d['landing']=dict(frame=fl,left_foot_y=float(J('left_foot_index',fl)[1]),into_court=float(J('left_foot_index',fl)[1]-BASE))
d['stance']=dict(front_foot_y_at_start=float(J('left_foot_index',0)[1]-BASE),hip_y_start=float(((J('left_hip',0)+J('right_hip',0))/2)[1]-BASE))
d['jump']=dict(max_foot_z=float(max(S['ankLz'][int(tc)-3:fl].max(),S['ankRz'][int(tc)-3:fl].max())))
json.dump(d,open(SP+'/sw/pl/ana/metrics.json','w'),indent=1,default=float)
def pr(o,ind=0):
    for k,v in o.items():
        if isinstance(v,dict): print(' '*ind+k); pr(v,ind+2)
        else: print(' '*ind+k+':', (round(v,3) if isinstance(v,float) else v))
pr(d)
