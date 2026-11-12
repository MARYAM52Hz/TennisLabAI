import sys, numpy as np, pickle, json
SP = __import__('os').environ['REEL_JOB']; JC = __import__('json').load(open(SP + '/job.json')); sys.path.insert(0,SP+'/nq'); sys.path.insert(0,SP+'/nq/ana'); sys.path.insert(0,SP+'/sw')
from series import build, ang, nrm, DT, tsec
from scipy.signal import savgol_filter
import ball as BL
T_of=BL.T_of
M,S=build(); lab=pickle.load(open(SP+'/sw/lab2.pkl','rb')); bl=pickle.load(open(SP+'/sw/ball3d.pkl','rb'))['S']
sm={k:savgol_filter(v,7,2) for k,v in S.items()}; BASE=-11.885
at=lambda k,f: float(np.interp(f,np.arange(M.T),sm[k])); J=lambda n,f: M.jf(n,f); tc=M.tc
w=np.arange(JC['trophy_w0'],JC['trophy_w1']); kn=(sm['kneeL']+sm['kneeR'])/2; tr=int(w[np.argmax(kn[w])])
wl=np.arange(tr+1,int(tc)-1); lo=int(wl[np.argmin(sm['rackZ'][wl]+ (np.arange(len(sm['rackZ']))[wl]<tr+3)*9)])
zL=np.array([J('left_ankle',f)[2] for f in range(M.T)]); land=[f for f in range(int(tc)+1,M.T) if zL[f]<0.14]; fl=land[0] if land else int(tc)+5
p2=lambda n,f: np.array(lab['skel'][n][f],float)
def elbow2d(f): return 180-ang(np.r_[p2('right_shoulder',f),0],np.r_[p2('right_elbow',f),0],np.r_[p2('right_wrist',f),0])
d=dict(events=dict(trophy=tr,low=lo,contact=round(tc,2),landing=fl))
d['times_ms']=dict(trophy_to_contact=round((tsec(tc)-tsec(tr))*1000),low_to_contact=round((tsec(tc)-tsec(lo))*1000))
d['trophy']=dict(kneeFront=at('kneeL',tr),kneeBack=at('kneeR',tr),trunkInc=at('trunkInc',tr),shTilt=at('shTilt',tr))
d['low']=dict(elbow2D=float(elbow2d(lo)),elbow3D=at('elbowR',lo),rackZ=at('rackZ',lo))
b=M.ball(tc); neck=J('top_spine',tc); hd=J('head',tc)
d['contact']=dict(ballXYZ=b.round(3).tolist(),height=float(b[2]),ahead=float(b[1]-BASE),elbow2D=float(elbow2d(int(round(tc)))),elbow3D=at('elbowR',tc),shTilt=at('shTilt',tc),trunkInc=at('trunkInc',tc),ball_ahead_of_head=float(b[1]-hd[1]),pelvisZ=at('pelvisZ',tc),headY=float(hd[1]),lean=float(np.degrees(np.arctan2((neck-J('bottom_spine',tc))[1],(neck-J('bottom_spine',tc))[2]))))
ts=np.linspace(JC['f0']-3,tc,800); zs=np.array([M.ball(t)[2] for t in ts]); i=int(np.argmax(zs)); pb=M.ball(ts[i]); neck_a=J('top_spine',ts[i]); hd_a=J('head',ts[i])
d['toss']=dict(apexFrame=float(ts[i]),apexZ=float(zs[i]),apex_ahead_of_head=float(pb[1]-hd_a[1]),apex_ahead_baseline=float(pb[1]-BASE),apex_to_contact_ms=float((tsec(tc)-tsec(ts[i]))*1000))
rel=[f for f in np.linspace(JC['f0']-3,JC['f0']+3,300) if M.ball(f)[2]>J('left_wrist',f)[2]+0.18]; d['toss']['release_frame']=float(rel[0]) if rel else None
v1=bl['v1']; sp=float(np.linalg.norm(v1)); fr=np.arange(bl['f0'],float(JC['N']-1),0.25); P=BL.positions(bl,fr); m=fr>=tc
z_net=float(np.interp(0,P[m,1],P[m,2])); ib=int(np.argmax((fr>tc)&(P[:,2]<0.06))); bounce=P[ib]
d['ball']=dict(speed_ms=sp,speed_kmh=sp*3.6,launch_deg=float(np.degrees(np.arcsin(v1[2]/sp))),lateral_deg=float(np.degrees(np.arctan2(v1[0],v1[1]))),net_clear=z_net-0.914,bounce_xy=bounce[:2].round(2).tolist(),bounce_frame=float(fr[ib]))
hv=(M.head_at(tc+0.25)-M.head_at(tc-0.25))/(2*0.25*DT); d['racket']=dict(head_speed_ms=float(np.linalg.norm(hv)),head_vz=float(hv[2]),head_vy=float(hv[1]),head_vx=float(hv[0]),path_up_deg=float(np.degrees(np.arctan2(hv[2],np.hypot(hv[0],hv[1])))))
d['landing']=dict(frame=fl,left_foot_y=float(J('left_foot_index',fl)[1]),into_court=float(J('left_foot_index',fl)[1]-BASE))
d['foot_at_toss_y']=float(J('left_foot_index',JC['f0']+1)[1]-BASE)
json.dump(d,open(SP+'/nq/ana/metrics.json','w'),indent=1,default=float)
def pr(o,ind=0):
    for k,v in o.items():
        if isinstance(v,dict): print(' '*ind+k); pr(v,ind+2)
        else: print(' '*ind+k+':', (round(v,3) if isinstance(v,float) else v))
pr(d)
