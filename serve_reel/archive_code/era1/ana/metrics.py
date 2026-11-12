import sys, numpy as np, pickle, json
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/lab2'); sys.path.insert(0,SP+'/ana')
from series import build, ang, yaw, nrm, DT
from scipy.signal import savgol_filter
M,S=build(); lab=pickle.load(open(SP+'/lab2/labels_ref.pkl','rb')); bl=pickle.load(open(SP+'/lab2/ball3d.pkl','rb'))
sm={k:savgol_filter(v,7,2) for k,v in S.items()}
BASE=-11.885
def at(k,f): return float(np.interp(f,np.arange(M.T),sm[k]))
J=lambda n,f: M.jf(n,f)
EV={'A':dict(trophy=12,low=20,tc=M.tcs['A'],rng=(0,60)),'B':dict(trophy=170,low=181,tc=M.tcs['B'],rng=(140,237))}
out={}
for k,e in EV.items():
    tc=e['tc']; tr=e['trophy']; lo=e['low']; d={}
    d['frames']=dict(trophy=tr,low=lo,contact=round(tc,2))
    d['times_ms']=dict(trophy_to_contact=round((tc-tr)*DT*1000),low_to_contact=round((tc-lo)*DT*1000))
    # --- trophy
    d['trophy']=dict(kneeFront=at('kneeL',tr),kneeBack=at('kneeR',tr),trunkInc=at('trunkInc',tr),trunkLat=at('trunkLat',tr),shTilt=at('shTilt',tr),
        elbowHit=at('elbowR',tr),elbowToss=at('elbowL',tr),tossArmElev=at('leftArmElev',tr),hitArmElev=at('shElevR',tr),pelvisZ=at('pelvisZ',tr),headZ=at('headZ',tr))
    d['low']=dict(elbowHit=at('elbowR',lo),rackZ=at('rackZ',lo),shoulderZ=float(J('right_shoulder',lo)[2]),elbowZ=float(J('right_elbow',lo)[2]),shTilt=at('shTilt',lo),trunkLat=at('trunkLat',lo),kneeFront=at('kneeL',lo),kneeBack=at('kneeR',lo),pelvisZ=at('pelvisZ',lo))
    # --- contact
    b=M.ball(tc); hd=M.head_at(tc); sh=J('right_shoulder',tc); wr=J('right_wrist',tc); el=J('right_elbow',tc)
    L1=np.linalg.norm(el-sh); L2=np.linalg.norm(wr-el)
    H=1.80
    d['contact']=dict(ballXYZ=b.round(3).tolist(),headXYZ=hd.round(3).tolist(),contactZ=float(b[2]),contactZ_over_H=float(b[2]/H),
        ahead_of_baseline=float(b[1]-BASE),
        elbowHit=at('elbowR',tc),shElevTrunk=at('shElevR',tc),armWorld=at('armWorldR',tc),shTilt=at('shTilt',tc),trunkLat=at('trunkLat',tc),trunkInc=at('trunkInc',tc),
        vertReach=float((wr[2]-sh[2])/(L1+L2)),armLen=float(L1+L2),shoulderZ=float(sh[2]),wristZ=float(wr[2]),
        ballFromShoulder_xy=(b[:2]-sh[:2]).round(3).tolist(),
        ballFromLeftHip_x=float(b[0]-J('left_hip',tc)[0]),ballFromBodyMid_x=float(b[0]-0.5*(J('left_hip',tc)[0]+J('right_hip',tc)[0])),
        ballFromLeftToe_y=float(b[1]-J('left_foot_index',tc)[1]),
        ankleL_z=float(J('left_ankle',tc)[2]),ankleR_z=float(J('right_ankle',tc)[2]),pelvisZ=at('pelvisZ',tc),pelvisRise=at('pelvisZ',tc)-at('pelvisZ',tr))
    # --- ball: toss + launch
    F=bl['A'] if k=='A' else bl['B2']; v1=F['v1']; sp=float(np.linalg.norm(v1))
    ts=np.linspace(e['rng'][0],tc,2000); zs=np.array([M.ball(t)[2] for t in ts]); okm=zs>-10; i=np.argmax(np.where(okm,zs,-1)); apex=ts[i]
    pb=M.ball(apex)
    d['toss']=dict(apexFrame=float(apex),apexZ=float(zs[i]),apexXY=pb[:2].round(3).tolist(),apex_to_contact_ms=float((tc-apex)*DT*1000),dropToContact=float(zs[i]-b[2]),
        apex_from_leftHip_x_at_trophy=float(pb[0]-J('left_hip',tr)[0]),apex_ahead_baseline=float(pb[1]-BASE),
        vz_at_contact=float((M.ball(tc+0.1)[2]-M.ball(tc-0.1)[2])/(0.2*DT)) )
    d['ball']=dict(speed_ms=sp,speed_kmh=sp*3.6,launch_down_deg=float(np.degrees(np.arcsin(v1[2]/sp))),launch_dir_deg_from_center=float(np.degrees(np.arctan2(v1[0],v1[1]))))
    # --- racket speed
    fr=np.arange(max(0,int(tc)-6),int(tc)+7)
    d['racket']=dict(headSpeed_at_contact=at('rackSpeed',tc),headSpeed_peak=float(sm['rackSpeed'][fr].max()),peak_frame=int(fr[np.argmax(sm['rackSpeed'][fr])]))
    # --- kinetic chain: peak speeds (smoothed) in window trophy..contact+5
    w=np.arange(tr,int(tc)+6)
    ch={}
    for nm in ['pelvSpeed','shSpeed','elbowSpeed','wristSpeed','rackSpeed']:
        j=w[np.argmax(sm[nm][w])]; ch[nm]=dict(frame=int(j),ms_before_contact=float((tc-j)*DT*1000),peak=float(sm[nm][j]))
    # angular: hip yaw, shoulder yaw rates (unwrapped, deg/s), elbow extension rate
    for nm in ['hipYaw','shYaw']:
        u=np.unwrap(np.radians(S[nm])); u=savgol_filter(np.degrees(u),7,2); r=np.abs(np.gradient(u))/DT; j=w[np.argmax(r[w])]; ch[nm+'Rate']=dict(frame=int(j),ms_before_contact=float((tc-j)*DT*1000),peak=float(r[j]))
    r=np.abs(np.gradient(sm['elbowR']))/DT; j=w[np.argmax(r[w])]; ch['elbowRate']=dict(frame=int(j),ms_before_contact=float((tc-j)*DT*1000),peak=float(r[j]))
    d['chain']=ch
    # --- landing
    zL=np.array([J('left_ankle',f)[2] for f in range(M.T)]); land=[f for f in range(int(tc),e['rng'][1]) if zL[f]<0.14]; fl=land[0] if land else None
    if fl is not None: d['landing']=dict(frame=fl,left_foot_y=float(J('left_foot_index',fl)[1]),into_court=float(J('left_foot_index',fl)[1]-BASE),flight_ms=float((fl-int(tc))*DT*1000))
    # --- 2D elbow check (image plane)  using labels in the ref frame
    def p2(n,f): return np.array(lab['skel'][n][f][0],float)
    f0=int(round(tc)); a=p2('right_shoulder',f0); bb=p2('right_elbow',f0); c=p2('right_wrist',f0)
    d['contact']['elbow2D_interior']=float(ang(np.r_[a,0],np.r_[bb,0],np.r_[c,0]))
    out[k]=d
json.dump(out,open(SP+'/ana/metrics.json','w'),indent=1,default=float)
def pr(o,ind=0):
    for k,v in o.items():
        if isinstance(v,dict): print(' '*ind+k); pr(v,ind+2)
        else: print(' '*ind+k+':', (round(v,2) if isinstance(v,float) else v))
pr(out)
