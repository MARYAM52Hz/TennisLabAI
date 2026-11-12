"""Joint-exact retargeting: the rig is *fitted* to the labelled skeleton, not just rotated towards it.
Every bone is rotated AND stretched along its own axis so that its head/tail land exactly on the lifted label joints
(shoulder, elbow, wrist, hip, knee, ankle, heel, toe, finger, spine ends).  Requires bone.inherit_scale = 'NONE' on every bone
(a stretched parent then moves the child's head to its new tail but does not scale the child).
RigPoser2(rig_info.json).pose_exact(J, look_at) -> {bone: 4x4 pose matrix (with Y scale)};  .basis_exact(P) -> {bone: 4x4 matrix_basis}"""
import numpy as np
from rigpose import RigPoser, nrm, arc, slerp_rot, axis_angle
import math


class RigPoser2(RigPoser):
    def pose_exact(self, J, look_at=None, hand_twist=0.7, spine_t=(0.2, 0.5, 0.8, 1.0), head_limits=(0.9, 1.1, -0.6)):
        Rc, Rp, _ = self.frames(J); Rot, Hd, Sc, Tl = {}, {}, {}, {}
        P0, TS = J['bottom_spine'], J['top_spine']

        def put(n, R, head, s=1.0):
            Rot[n] = R; Hd[n] = head; Sc[n] = s; Tl[n] = head + s * (R @ (self.T0[n] - self.H0[n]))

        def reach(n, Rparent, head, target, frac=1.0, extra=0.0):
            """rotate bone n (child of a frame Rparent) to point at target and stretch so the tail is at head + frac*(target-head)"""
            d = (target - head) * frac; R = arc(Rparent @ self.y0[n], d) @ Rparent; put(n, R, head, np.linalg.norm(d) / max(self.len[n], 1e-9)); return R
        # --- spine: keep the natural bend, then align + stretch the whole chain so it runs exactly bottom_spine -> top_spine
        names = ('Bone', 'Bone.001', 'Bone.002', 'Bone.003'); rots = [slerp_rot(Rp, Rc, t) for t in spine_t]
        V0 = sum(R @ (self.T0[n] - self.H0[n]) for R, n in zip(rots, names)); Q = arc(V0, TS - P0); s = np.linalg.norm(TS - P0) / np.linalg.norm(V0); head = P0
        for R, n in zip(rots, names): put(n, Q @ R, head, s); head = Tl[n]
        Rc = Q @ Rc
        # --- clavicle -> humerus -> forearm -> palm -> fingers (all label joints reached exactly)
        for s_ in ('L', 'R'):
            side = 'left' if s_ == 'L' else 'right'; Sj, Ej, Wj = J[f'{side}_shoulder'], J[f'{side}_elbow'], J[f'{side}_wrist']; ix, tb = J[f'{side}_index'], J[f'{side}_thumb']
            Rcl = reach(f'Shoulder_{s_}', Rc, TS, Sj)
            Rh = reach(f'Humerus_{s_}', Rcl, Sj, Ej); Rf = reach(f'Forearm_{s_}', Rh, Ej, Wj)
            dirp = nrm(ix - Wj); Rpl = arc(Rf @ self.y0[f'Palm_{s_}'], dirp) @ Rf
            tdir = tb - Wj; tdir = tdir - dirp * np.dot(tdir, dirp)                       # thumb side -> twist the palm
            if np.linalg.norm(tdir) > 1e-4 and hand_twist > 0:
                cur = Rpl @ self.R0[f'Palm_{s_}'].T @ np.array([1.0, 0, 0]); cur = cur - dirp * np.dot(cur, dirp)
                if np.linalg.norm(cur) > 1e-6:
                    ang = math.atan2(np.dot(np.cross(nrm(cur), nrm(tdir)), dirp), np.dot(nrm(cur), nrm(tdir))); Rpl = axis_angle(dirp, float(np.clip(ang, -1.2, 1.2)) * hand_twist) @ Rpl
            lp, lf = self.len[f'Palm_{s_}'], self.len[f'Fingers_{s_}']; frac = lp / (lp + lf)
            put(f'Palm_{s_}', Rpl, Wj, np.linalg.norm(ix - Wj) * frac / lp)
            reach(f'Fingers_{s_}', Rpl, Tl[f'Palm_{s_}'], ix)
        # --- pelvis spurs -> femur -> tibia -> heel -> sole -> toes
        for s_ in ('L', 'R'):
            side = 'left' if s_ == 'L' else 'right'; Hj, Kj, Aj, hl, fi = J[f'{side}_hip'], J[f'{side}_knee'], J[f'{side}_ankle'], J[f'{side}_heel'], J[f'{side}_foot_index']
            Rpv = reach(f'Pelvic_{s_}', Rp, P0, Hj); Rfm = reach(f'Femur_{s_}', Rpv, Hj, Kj); Rtb = reach(f'Tibia_{s_}', Rfm, Kj, Aj); Rhl = reach(f'Heel_{s_}', Rtb, Aj, hl)
            ls, lt = self.len[f'Sole_{s_}'], self.len[f'Toes_{s_}']; Rso = reach(f'Sole_{s_}', Rhl, hl, fi, frac=ls / (ls + lt)); reach(f'Toes_{s_}', Rso, Tl[f'Sole_{s_}'], fi)
        # --- neck + head (no head landmarks: natural look-at, unscaled)
        Rhd = Rc
        if look_at is not None:
            hc = Tl['Bone.003'] + (Rc @ self.y0['Bone.026']) * self.len['Bone.026']; l = nrm(look_at - hc); lc = Rc.T @ l
            yaw = math.atan2(lc[1], lc[0]); pitch = math.asin(float(np.clip(lc[2], -1, 1)))
            yaw = float(np.clip(yaw, -head_limits[0], head_limits[0])) * 0.8; pitch = float(np.clip(pitch, head_limits[2], head_limits[1])) * 0.75
            Rhd = Rc @ axis_angle([0, 0, 1], yaw) @ axis_angle([0, 1, 0], -pitch)
        put('Bone.026', slerp_rot(Rc, Rhd, 0.45), Tl['Bone.003']); put('Bone.027', Rhd, Tl['Bone.026'])
        P = {}
        for n in self.names:
            M = np.eye(4); M[:3, :3] = (Rot[n] @ self.R0[n]) @ np.diag([1.0, Sc[n], 1.0]); M[:3, 3] = Hd[n]; P[n] = M
        self.last_scale = Sc
        return P

    def basis_exact(self, P):
        """matrix_basis per bone for inherit_scale == 'NONE' (parent contributes its rotation and its stretched tail, not its scale)."""
        B = {}
        for n in self.order:
            p = self.par[n]
            if p is None: B[n] = np.linalg.inv(self.O[n]) @ P[n]; continue
            rel = np.linalg.inv(self.O[p]) @ self.O[n]; Pp = P[p]; sp = float(np.linalg.norm(Pp[:3, 1]))                        # parent's own Y stretch
            Rp_ns = Pp[:3, :3] @ np.diag([1.0, 1.0 / sp, 1.0]); head_base = Pp[:3, 3] + Pp[:3, :3] @ rel[:3, 3]; R_pre = Rp_ns @ rel[:3, :3]
            Rn = P[n][:3, :3]; sn = float(np.linalg.norm(Rn[:, 1])); Rn_ns = Rn @ np.diag([1.0, 1.0 / sn, 1.0])
            M = np.eye(4); M[:3, :3] = (R_pre.T @ Rn_ns) @ np.diag([1.0, sn, 1.0]); M[:3, 3] = R_pre.T @ (P[n][:3, 3] - head_base); B[n] = M
        return B
