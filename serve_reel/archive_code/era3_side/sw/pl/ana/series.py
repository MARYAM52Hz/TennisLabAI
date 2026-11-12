"""Per-frame biomechanical series for both serves from the 3D reconstruction (Motion2)."""
import sys, numpy as np, pickle
SP='/tmp/claude-0/-home-claude/2a0f4416-55f7-5d66-babf-bfd62e72f7df/scratchpad'; sys.path.insert(0,SP+'/sw/pl'); sys.path.insert(0,SP+'/sw')
from motion_sw import Motion2, nrm
DT=1/30.
def tsec(f): return float(f)/30.0                 # unique-frame index -> real time (30 fps capture, 5x slow-motion export)
def ang(a,b,c):                       # interior angle at b
    u=nrm(a-b); v=nrm(c-b); return np.degrees(np.arccos(np.clip(np.dot(u,v),-1,1)))
def yaw(v):                           # azimuth of a horizontal vector, 0 = +x (player's right when facing the net), +90 = toward the net (+y)
    return np.degrees(np.arctan2(v[1],v[0]))
def build(M=None):
    M=M or Motion2(); T=M.T; S={}
    J=lambda n,f: M.jf(n,f)
    rows={k:[] for k in ['kneeL','kneeR','elbowR','elbowL','shElevR','armWorldR','trunkInc','trunkLat','shTilt','hipYaw','shYaw','pelvisZ','headZ','rackZ','rackSpeed','wristSpeed','elbowSpeed','shSpeed','pelvSpeed','ankLz','ankRz','ballz','handZ','rackAngFromVert','leftArmElev']}
    for f in range(T):
        L=lambda n: J(n,f)
        rows['kneeL'].append(180-ang(L('left_hip'),L('left_knee'),L('left_ankle')))
        rows['kneeR'].append(180-ang(L('right_hip'),L('right_knee'),L('right_ankle')))
        rows['elbowR'].append(180-ang(L('right_shoulder'),L('right_elbow'),L('right_wrist')))
        rows['elbowL'].append(180-ang(L('left_shoulder'),L('left_elbow'),L('left_wrist')))
        up=nrm(L('top_spine')-L('bottom_spine'))
        ua=nrm(L('right_elbow')-L('right_shoulder'))
        rows['shElevR'].append(np.degrees(np.arccos(np.clip(np.dot(ua,-up),-1,1))))      # humerus vs trunk-down axis (0 = arm hanging, 180 = overhead)
        rows['armWorldR'].append(np.degrees(np.arccos(np.clip(ua[2],-1,1))))             # humerus vs world up
        rows['leftArmElev'].append(np.degrees(np.arccos(np.clip(np.dot(nrm(L('left_elbow')-L('left_shoulder')),-up),-1,1))))
        rows['trunkInc'].append(np.degrees(np.arccos(np.clip(up[2],-1,1))))
        # lateral (frontal-plane) trunk tilt: component of the trunk axis along the court x (player's right), signed + when leaning to the left (away from racket arm)
        rows['trunkLat'].append(np.degrees(np.arctan2(-up[0],up[2])))
        sh=L('right_shoulder')-L('left_shoulder'); hp=L('right_hip')-L('left_hip')
        rows['shTilt'].append(np.degrees(np.arctan2(sh[2],np.hypot(sh[0],sh[1]))))
        rows['shYaw'].append(yaw(sh)); rows['hipYaw'].append(yaw(hp))
        rows['pelvisZ'].append(L('bottom_spine')[2]); rows['headZ'].append(L('head')[2])
        rows['rackZ'].append(M.head_at(f)[2]); rows['ankLz'].append(L('left_ankle')[2]); rows['ankRz'].append(L('right_ankle')[2]); rows['ballz'].append(M.ball(f)[2])
        rows['handZ'].append(L('left_wrist')[2])
        rows['rackAngFromVert'].append(0)
    S={k:np.array(v) for k,v in rows.items()}
    # speeds (central difference of the spline) in m/s, 30 fps clock
    def speed(fn,f,h=0.25): return np.linalg.norm(fn(min(f+h,T-1))-fn(max(f-h,0)))/(tsec(min(f+h,T-1))-tsec(max(f-h,0)))
    S['rackSpeed']=np.array([speed(M.head_at,f) for f in range(T)])
    S['wristSpeed']=np.array([speed(lambda t:M.jf('right_wrist',t),f) for f in range(T)])
    S['elbowSpeed']=np.array([speed(lambda t:M.jf('right_elbow',t),f) for f in range(T)])
    S['shSpeed']=np.array([speed(lambda t:M.jf('right_shoulder',t),f) for f in range(T)])
    S['pelvSpeed']=np.array([speed(lambda t:M.jf('bottom_spine',t),f) for f in range(T)])
    return M,S
if __name__=='__main__':
    M,S=build(); pickle.dump(S,open(SP+'/sw/pl/ana/series.pkl','wb'))
    np.set_printoptions(linewidth=200,precision=1,suppress=True)
    for name,(a,b) in {'A':(0,60),'B':(140,237)}.items():
        print('=== serve',name)
        for k in ['kneeL','kneeR','elbowR','shElevR','trunkInc','trunkLat','shTilt','shYaw','hipYaw','pelvisZ','rackZ','rackSpeed','ballz','handZ']:
            print(k.ljust(10),S[k][a:b:3])
