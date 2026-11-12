import sys, numpy as np, pickle, json
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/ns'); sys.path.insert(0,SP+'/ns/ana'); sys.path.insert(0,SP+'/sw')
from series import build, ang, nrm, DT, tsec
from scipy.signal import savgol_filter
import ball as BL
T_of=BL.T_of
M,S=build(); lab=pickle.load(open(SP+'/sw/labels2.pkl','rb')); bl=pickle.load(open(SP+'/sw/ball3d.pkl','rb'))['S']
sm={k:savgol_filter(v,7,2) for k,v in S.items()}; BASE=-11.885
at=lambda k,f: float(np.interp(f,np.arange(M.T),sm[k])); J=lambda n,f: M.jf(n,f); tc=M.tc
# --- events
w=np.arange(12,27); kn=(sm['kneeL']+sm['kneeR'])/2; tr=int(w[np.argmax(kn[w])])
rz=S['rackZ']; pk=tr+int(np.argmax(rz[tr:int(tc)-3])); wl=np.arange(pk,int(tc)-1); lo=int(wl[np.argmin(rz[wl])]); print('tr',tr,'pk',pk,'lo',lo)
zR=np.array([J('right_ankle',f)[2] for f in range(M.T)]); land=[f for f in range(int(tc)+8,M.T) if zR[f]<0.21]; fl=land[0] if land else int(tc)+18
p2=lambda n,f: np.array(lab['skel'][n][f],float)
def elbow2d(f): return 180-ang(np.r_[p2('right_shoulder',f),0],np.r_[p2('right_elbow',f),0],np.r_[p2('right_wrist',f),0])
d=dict(events=dict(trophy=tr,low=lo,contact=round(tc,2),landing=fl))
d['times_ms']=dict(trophy_to_contact=round((tsec(tc)-tsec(tr))*1000),low_to_contact=round((tsec(tc)-tsec(lo))*1000))
d['trophy']=dict(kneeFront=at('kneeL',tr),kneeBack=at('kneeR',tr),trunkInc=at('trunkInc',tr),shTilt=at('shTilt',tr))
d['low']=dict(elbow2D=float(elbow2d(lo)),elbow3D=at('elbowR',lo),rackZ=at('rackZ',lo))
b=M.ball(tc); sh=J('right_shoulder',tc); neck=J('top_spine',tc)
d['contact']=dict(ballXYZ=b.round(3).tolist(),height=float(b[2]),ahead=float(b[1]-BASE),elbow2D=float(elbow2d(int(round(tc)))),shTilt=at('shTilt',tc),trunkInc=at('trunkInc',tc),ball_minus_neck_y=float(b[1]-neck[1]),ball_minus_head_y=float(b[1]-J('head',tc)[1]),pelvisZ=at('pelvisZ',tc))
ts=np.linspace(5,tc,800); zs=np.array([M.ball(t)[2] for t in ts]); i=int(np.argmax(zs)); pb=M.ball(ts[i]); neck_a=J('top_spine',ts[i])
d['toss']=dict(apexFrame=float(ts[i]),apexZ=float(zs[i]),apex_minus_neck_y=float(pb[1]-neck_a[1]),apex_minus_head_y=float(pb[1]-J('head',ts[i])[1]),apex_to_contact_ms=float((tsec(tc)-tsec(ts[i]))*1000),apex_ahead_baseline=float(pb[1]-BASE))
v1=bl['v1']; sp=float(np.linalg.norm(v1)); fr=np.arange(bl['f0'],62.0,0.25); P=BL.positions(bl,fr); m=fr>=tc
z_net=float(np.interp(0,P[m,1],P[m,2])); ib=int(np.argmax((fr>tc)&(P[:,2]<0.06))) ; bounce=P[ib]
d['ball']=dict(speed_ms=sp,speed_kmh=sp*3.6,launch_deg=float(np.degrees(np.arcsin(v1[2]/sp))),lateral_deg=float(np.degrees(np.arctan2(v1[0],v1[1]))),net_clear=z_net-0.914,bounce_xy=bounce[:2].round(2).tolist(),bounce_frame=float(fr[ib]))
hp=lambda k: np.array(lab['face'][k][:2],float); dv=hp(33)-hp(31); dv0=hp(32)-hp(31); dv1=hp(33)-hp(32)
d['racket_2d']=dict(face_ratio_contact=float(min(lab['face'][32][2:4])/max(lab['face'][32][2:4])),path_up_deg=float(np.degrees(np.arctan2(-dv[1],dv[0]))),path_up_before=float(np.degrees(np.arctan2(-dv0[1],dv0[0]))),path_up_after=float(np.degrees(np.arctan2(-dv1[1],dv1[0]))))
d['head_speed_ms']=float(S['rackSpeed'][32])
d['landing']=dict(frame=fl,foot_y=float(J('right_foot_index',fl)[1]),into_court=float(J('right_foot_index',fl)[1]-BASE))
d['foot_at_toss_y']=float(J('left_foot_index',5)[1]-BASE)
d['seq_peak_frames']={k:int(np.argmax(sm[k][15:40]))+15 for k in ('pelvSpeed','shSpeed','elbowSpeed','wristSpeed','rackSpeed')}
json.dump(d,open(SP+'/ns/ana/metrics.json','w'),indent=1,default=float)
def pr(o,ind=0):
    for k,v in o.items():
        if isinstance(v,dict): print(' '*ind+k); pr(v,ind+2)
        else: print(' '*ind+k+':', (round(v,3) if isinstance(v,float) else v))
pr(d)
