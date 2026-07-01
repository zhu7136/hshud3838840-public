#!/usr/bin/env python
"""Retarget G1 OmniRetarget trajectory to HU_D04 via per-frame Jacobian IK.

Loads G1 qpos (already solved for the 50cm climb_14 terrain by OmniRetarget),
runs G1 forward kinematics to extract world positions of 14 tracked bodies,
then solves hu_d04's joint angles (and root position) to place hu_d04's
corresponding bodies at the same world positions — preserving the task
(foot/hand contacts on terrain) while adapting to hu_d04's proportions.

Usage:
    python retarget_g1_to_hu_d04_ik.py \
        --input /workspace/holosoma/OmniRetarget_Dataset/robot-terrain/climb_14_z_scale_1.0_robot_only.npz \
        --output holosoma/data/motions/hu_d04_29dof/whole_body_tracking/climb_14_holosoma.npz
"""

from __future__ import annotations

import argparse
from pathlib import Path

import mujoco
import numpy as np


# ── Body mapping: G1 body → hu_d04 body, with weights ──
# End-effectors (feet tips, hands, root) get high weight (critical for task).
# Intermediate bodies (knees, elbows, etc.) get low weight (geometry differs,
# so exact match is impossible — they provide directional guidance only).
BODY_MAPPING = [
    # (g1_body, hu_d04_body, weight)
    # Track JOINT CENTERS (not end-effector tips) to avoid forcing joints to
    # compensate for differing foot/hand geometry between G1 and hu_d04.
    # Use MODERATE weights on ankles (not high) to prevent hip_yaw compensation
    # for hip-width differences.
    ("pelvis", "base_link", 5.0),                              # root position
    ("left_hip_roll_link", "left_hip_roll_link", 1.0),
    ("left_knee_link", "left_knee_link", 1.0),
    ("left_ankle_roll_link", "left_ankle_roll_link", 2.0),     # ankle joint center
    ("right_hip_roll_link", "right_hip_roll_link", 1.0),
    ("right_knee_link", "right_knee_link", 1.0),
    ("right_ankle_roll_link", "right_ankle_roll_link", 2.0),   # ankle joint center
    ("torso_link", "waist_pitch_link", 1.0),
    ("left_shoulder_roll_link", "left_shoulder_roll_link", 0.5),
    ("left_elbow_link", "left_elbow_link", 0.3),
    ("left_wrist_roll_link", "left_wrist_roll_link", 0.5),     # wrist joint center
    ("right_shoulder_roll_link", "right_shoulder_roll_link", 0.5),
    ("right_elbow_link", "right_elbow_link", 0.3),
    ("right_wrist_roll_link", "right_wrist_roll_link", 0.5),   # wrist joint center
]

# hu_d04 31dof model: head joints at qpos indices 22, 23 (fixed to 0)
HEAD_QPOS_INDICES = [22, 23]


def solve_ik_frame(
    hd_model: mujoco.MjModel,
    hd_data: mujoco.MjData,
    target_positions: np.ndarray,  # (N, 3)
    hd_body_ids: list[int],       # N body ids in hd_model
    body_weights: np.ndarray,     # (N,) weights for each body
    q_init: np.ndarray,           # (38,) initial qpos
    root_quat: np.ndarray,        # (4,) fixed root quaternion (wxyz)
    qpos_lb: np.ndarray,          # (nq,) joint lower bounds
    qpos_ub: np.ndarray,          # (nq,) joint upper bounds
    max_iters: int = 100,
    tol: float = 1e-4,
    trust_region: float = 0.1,
) -> tuple[np.ndarray, float]:
    """Solve IK for one frame. Returns (qpos, max_error)."""
    q = q_init.copy()
    q[3:7] = root_quat  # fix root orientation
    q[HEAD_QPOS_INDICES] = 0.0  # fix head

    jac_pos = np.zeros((3, hd_model.nv))
    jac_rot = np.zeros((3, hd_model.nv))
    max_err = float("inf")

    # Build IK qvel indices: root linear (0,1,2) + all non-head hinge joints
    ik_dof_indices = [0, 1, 2]  # root linear velocity
    ik_qpos_indices = [0, 1, 2]  # root position
    for i in range(hd_model.njnt):
        if hd_model.jnt_type[i] == mujoco.mjtJoint.mjJNT_FREE:
            continue
        jname = mujoco.mj_id2name(hd_model, mujoco.mjtObj.mjOBJ_JOINT, i)
        if jname in ("head_yaw_joint", "head_pitch_joint"):
            continue
        ik_dof_indices.append(hd_model.jnt_dofadr[i])
        ik_qpos_indices.append(hd_model.jnt_qposadr[i])
    ik_dof_indices = np.array(ik_dof_indices)  # (32,)
    ik_qpos_indices = np.array(ik_qpos_indices)  # (32,)

    # Weight matrix for weighted least squares
    W = np.sqrt(body_weights)  # (N,)
    n_bodies = len(hd_body_ids)

    for iteration in range(max_iters):
        q[3:7] = root_quat
        q[HEAD_QPOS_INDICES] = 0.0
        hd_data.qpos[:] = q
        mujoco.mj_forward(hd_model, hd_data)

        # Compute errors and Jacobians
        errors = []
        jac_rows = []
        for k, bid in enumerate(hd_body_ids):
            err = target_positions[k] - hd_data.xpos[bid]
            errors.append(err * W[k])  # apply weight to error
            mujoco.mj_jac(hd_model, hd_data, jac_pos, jac_rot, hd_data.xpos[bid], bid)
            jac_rows.append(jac_pos.copy() * W[k])  # apply weight to Jacobian

        e = np.concatenate(errors)  # (N*3,)
        J_full = np.vstack(jac_rows)  # (N*3, nv)
        J = J_full[:, ik_dof_indices]  # (N*3, 32)

        # Track unweighted error for convergence (max of weighted)
        raw_errors = np.concatenate([target_positions[k] - hd_data.xpos[bid] for k, bid in enumerate(hd_body_ids)])
        max_err = np.max(np.abs(raw_errors))
        if max_err < tol:
            break

        # Damped least squares (higher damping for stability, prevents extreme joints)
        # Add regularization toward q_init (warm start) to prevent extreme compensation
        # for geometric differences (hip width, shoulder position) between G1 and hu_d04.
        damping = 1e-2
        reg_weight = 0.5  # pull toward q_init
        q_prior = q_init[ik_qpos_indices] - q[ik_qpos_indices]  # (32,)
        # Augment: [J; reg*I] @ dq = [e; reg*q_prior]
        J_aug = np.vstack([J, reg_weight * np.eye(len(ik_dof_indices))])
        e_aug = np.concatenate([e, reg_weight * q_prior])
        JJt = J_aug @ J_aug.T + damping * np.eye(J_aug.shape[0])
        dq = J_aug.T @ np.linalg.solve(JJt, e_aug)  # (32,)

        # Trust region
        max_dq = np.max(np.abs(dq))
        if max_dq > trust_region:
            dq *= trust_region / max_dq

        # Apply update
        for k_idx, qpos_idx in enumerate(ik_qpos_indices):
            q[qpos_idx] += dq[k_idx]
            q[qpos_idx] = np.clip(q[qpos_idx], qpos_lb[qpos_idx], qpos_ub[qpos_idx])

    q[3:7] = root_quat
    q[HEAD_QPOS_INDICES] = 0.0
    return q, max_err


def compute_body_kinematics(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    qpos_trajectory: np.ndarray,  # (T, nq)
    fps: float,
) -> dict:
    """Compute body world positions, quaternions, and velocities for all frames."""
    T = qpos_trajectory.shape[0]
    nbody = model.nbody
    dt = 1.0 / fps

    body_pos_w = np.zeros((T, nbody, 3))
    body_quat_w = np.zeros((T, nbody, 4))
    body_lin_vel_w = np.zeros((T, nbody, 3))
    body_ang_vel_w = np.zeros((T, nbody, 3))

    for t in range(T):
        data.qpos[:] = qpos_trajectory[t]
        data.qvel[:] = 0.0
        mujoco.mj_forward(model, data)
        body_pos_w[t] = data.xpos[:]
        body_quat_w[t] = data.xquat[:]

    # Velocities via finite differences
    for t in range(T):
        if t == 0:
            body_lin_vel_w[t] = body_lin_vel_w[1] if T > 1 else 0
            body_ang_vel_w[t] = body_ang_vel_w[1] if T > 1 else 0
        elif t == T - 1:
            body_lin_vel_w[t] = body_lin_vel_w[t - 1]
            body_ang_vel_w[t] = body_ang_vel_w[t - 1]
        else:
            body_lin_vel_w[t] = (body_pos_w[t + 1] - body_pos_w[t - 1]) / (2 * dt)
            # Angular velocity from quaternion difference (approximate)
            for b in range(nbody):
                q0 = body_quat_w[t - 1, b]  # wxyz
                q1 = body_quat_w[t + 1, b]
                q0_conj = np.array([q0[0], -q0[1], -q0[2], -q0[3]])
                # q_rel = q1 * q0^{-1}
                w0, x0, y0, z0 = q1
                w1, x1, y1, z1 = q0_conj
                q_rel = np.array([
                    w0*w1 - x0*x1 - y0*y1 - z0*z1,
                    w0*x1 + x0*w1 + y0*z1 - z0*y1,
                    w0*y1 - x0*z1 + y0*w1 + z0*x1,
                    w0*z1 + x0*y1 - y0*x1 + z0*w1,
                ])
                q_rel = q_rel / (np.linalg.norm(q_rel) + 1e-12)
                w = np.clip(q_rel[0], -1.0, 1.0)
                angle = 2.0 * np.arccos(w)
                s = np.sqrt(max(0.0, 1.0 - w * w))
                if s > 1e-8:
                    axis = q_rel[1:] / s
                else:
                    axis = np.zeros(3)
                body_ang_vel_w[t, b] = axis * angle / (2 * dt)

    return {
        "body_pos_w": body_pos_w,
        "body_quat_w": body_quat_w,
        "body_lin_vel_w": body_lin_vel_w,
        "body_ang_vel_w": body_ang_vel_w,
    }


def convert(
    input_path: str,
    output_path: str,
    g1_xml: str,
    hu_d04_xml: str,
    max_iters: int = 100,
    tol: float = 1e-4,
    trust_region: float = 0.1,
):
    """Convert G1 OmniRetarget NPZ to HU_D04 holosoma NPZ via IK."""
    # Load G1 data
    g1_data_npz = np.load(input_path)
    g1_qpos_omni = g1_data_npz["qpos"]  # (T, 36) = [quat4, pos3, joints29]
    fps = float(g1_data_npz["fps"])
    T = g1_qpos_omni.shape[0]
    print(f"Loaded {input_path}: T={T}, fps={fps}, qpos={g1_qpos_omni.shape}")

    # Load models
    g1_model = mujoco.MjModel.from_xml_path(g1_xml)
    g1_data = mujoco.MjData(g1_model)
    hd_model = mujoco.MjModel.from_xml_path(hu_d04_xml)
    hd_data = mujoco.MjData(hd_model)
    print(f"G1 model: nbody={g1_model.nbody}, nq={g1_model.nq}")
    print(f"HU_D04 model: nbody={hd_model.nbody}, nq={hd_model.nq}")

    # Get body ids
    g1_bnames = [mujoco.mj_id2name(g1_model, mujoco.mjtObj.mjOBJ_BODY, i) for i in range(g1_model.nbody)]
    hd_bnames = [mujoco.mj_id2name(hd_model, mujoco.mjtObj.mjOBJ_BODY, i) for i in range(hd_model.nbody)]

    g1_body_ids = []
    hd_body_ids = []
    body_weights = []
    for g1_name, hd_name, weight in BODY_MAPPING:
        assert g1_name in g1_bnames, f"G1 body '{g1_name}' not found in model"
        assert hd_name in hd_bnames, f"HU_D04 body '{hd_name}' not found in model"
        g1_body_ids.append(g1_bnames.index(g1_name))
        hd_body_ids.append(hd_bnames.index(hd_name))
        body_weights.append(weight)
    body_weights = np.array(body_weights)
    print(f"Tracked body pairs: {len(BODY_MAPPING)}")

    # Joint limits for clipping (computed once)
    qpos_lb = np.full(hd_model.nq, -np.inf)
    qpos_ub = np.full(hd_model.nq, np.inf)
    for i in range(hd_model.njnt):
        if hd_model.jnt_type[i] == mujoco.mjtJoint.mjJNT_FREE:
            continue
        qadr = hd_model.jnt_qposadr[i]
        qpos_lb[qadr] = hd_model.jnt_range[i][0]
        qpos_ub[qadr] = hd_model.jnt_range[i][1]

    # Solve IK per frame
    hd_qpos_all = np.zeros((T, hd_model.nq))  # (T, 38)
    q_init = np.zeros(hd_model.nq)
    q_init[3] = 1.0  # identity quaternion

    errors_log = []
    for t in range(T):
        # G1 FK: reorder [quat4, pos3, joints] → [pos3, quat4, joints]
        g1_qpos_mj = np.zeros(g1_model.nq)
        g1_qpos_mj[:3] = g1_qpos_omni[t, 4:7]    # pos
        g1_qpos_mj[3:7] = g1_qpos_omni[t, 0:4]   # quat (wxyz)
        g1_qpos_mj[7:] = g1_qpos_omni[t, 7:]     # joints
        g1_data.qpos[:] = g1_qpos_mj
        mujoco.mj_forward(g1_model, g1_data)

        # Extract target positions from G1
        target_positions = np.array([g1_data.xpos[bid] for bid in g1_body_ids])  # (14, 3)

        # Root quaternion from G1 (both robots have identity base frame)
        root_quat = g1_qpos_omni[t, 0:4].copy()  # wxyz

        # Initialize: frame 0 from G1 root pos + legs/waist joints (arms solved by IK),
        # else from previous solution (warm start)
        if t == 0:
            q_init = np.zeros(hd_model.nq)
            q_init[3] = 1.0  # identity quat
            q_init[:3] = g1_qpos_omni[t, 4:7]  # start from G1 root pos
            # Legs + waist: G1 and hu_d04 have identical joint order for [0:15]
            g1_joints = g1_qpos_omni[t, 7:]  # 29 G1 joints
            q_init[7:22] = g1_joints[:15]  # legs(12) + waist(3) — same order
            # Arms: rough init (IK will refine). G1 wrist order is roll,pitch,yaw;
            # hu_d04 wrist order is yaw,pitch,roll. Map accordingly.
            # G1 L_arm[15:22] = shoulder(3)+elbow+wrist_roll+wrist_pitch+wrist_yaw
            # hu_d04 L_arm qpos[24:31] = shoulder(3)+elbow+wrist_yaw+wrist_pitch+wrist_roll
            q_init[24:28] = g1_joints[15:19]  # shoulder(3) + elbow
            q_init[24] = g1_joints[15]   # L shoulder pitch
            q_init[25] = g1_joints[16]   # L shoulder roll
            q_init[26] = g1_joints[17]   # L shoulder yaw
            q_init[27] = g1_joints[18]   # L elbow
            q_init[28] = g1_joints[21]   # L wrist yaw <- G1 wrist_yaw
            q_init[29] = g1_joints[20]   # L wrist pitch <- G1 wrist_pitch
            q_init[30] = g1_joints[19]   # L wrist roll <- G1 wrist_roll
            # R_arm: G1[22:29] → hu_d04[31:38]
            q_init[31] = g1_joints[22]   # R shoulder pitch
            q_init[32] = g1_joints[23]   # R shoulder roll
            q_init[33] = g1_joints[24]   # R shoulder yaw
            q_init[34] = g1_joints[25]   # R elbow
            q_init[35] = g1_joints[28]   # R wrist yaw
            q_init[36] = g1_joints[27]   # R wrist pitch
            q_init[37] = g1_joints[26]   # R wrist roll
        # else: q_init is previous frame's solution

        q_solved, max_err = solve_ik_frame(
            hd_model, hd_data, target_positions, hd_body_ids, body_weights,
            q_init, root_quat, qpos_lb, qpos_ub, max_iters, tol, trust_region,
        )
        hd_qpos_all[t] = q_solved
        q_init = q_solved.copy()  # warm start next frame
        errors_log.append(max_err)

        if t % 50 == 0 or t == T - 1:
            print(f"  Frame {t}/{T}: max_err={max_err:.6f} m")

    errors_log = np.array(errors_log)
    print(f"\nIK complete: mean_err={errors_log.mean():.6f}, max_err={errors_log.max():.6f}")
    print(f"  frames > 1cm: {np.sum(errors_log > 0.01)}/{T}")
    print(f"  frames > 5cm: {np.sum(errors_log > 0.05)}/{T}")

    # Compute body kinematics
    print("\nComputing body kinematics...")
    body_kin = compute_body_kinematics(hd_model, hd_data, hd_qpos_all, fps)

    # Compute joint velocities
    dt = 1.0 / fps
    joint_pos_all = hd_qpos_all.copy()  # (T, 38)
    joint_vel_all = np.zeros((T, hd_model.nv))  # (T, 37)
    # root linear vel
    joint_vel_all[:, :3] = np.gradient(joint_pos_all[:, :3], dt, axis=0)
    # root angular vel (from quaternion)
    for t in range(1, T - 1):
        q0 = joint_pos_all[t - 1, 3:7]
        q1 = joint_pos_all[t + 1, 3:7]
        q0_conj = np.array([q0[0], -q0[1], -q0[2], -q0[3]])
        w0, x0, y0, z0 = q1
        w1, x1, y1, z1 = q0_conj
        q_rel = np.array([
            w0*w1 - x0*x1 - y0*y1 - z0*z1,
            w0*x1 + x0*w1 + y0*z1 - z0*y1,
            w0*y1 - x0*z1 + y0*w1 + z0*x1,
            w0*z1 + x0*y1 - y0*x1 + z0*w1,
        ])
        q_rel = q_rel / (np.linalg.norm(q_rel) + 1e-12)
        w = np.clip(q_rel[0], -1.0, 1.0)
        angle = 2.0 * np.arccos(w)
        s = np.sqrt(max(0.0, 1.0 - w * w))
        if s > 1e-8:
            axis = q_rel[1:] / s
        else:
            axis = np.zeros(3)
        joint_vel_all[t, 3:6] = axis * angle / (2 * dt)
    joint_vel_all[0, 3:6] = joint_vel_all[1, 3:6] if T > 1 else 0
    joint_vel_all[-1, 3:6] = joint_vel_all[-2, 3:6]
    # joint velocities (finite differences)
    joint_vel_all[:, 6:] = np.gradient(joint_pos_all[:, 7:], dt, axis=0)

    # Get joint and body names
    joint_names = []
    for i in range(hd_model.njnt):
        if hd_model.jnt_type[i] == mujoco.mjtJoint.mjJNT_FREE:
            continue
        joint_names.append(mujoco.mj_id2name(hd_model, mujoco.mjtObj.mjOBJ_JOINT, i))
    body_names = [mujoco.mj_id2name(hd_model, mujoco.mjtObj.mjOBJ_BODY, i) for i in range(hd_model.nbody)]

    # Save
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    np.savez(
        output_path,
        fps=np.float64(fps),
        joint_names=np.array(joint_names, dtype="U64"),
        body_names=np.array(body_names, dtype="U64"),
        joint_pos=joint_pos_all,
        joint_vel=joint_vel_all,
        body_pos_w=body_kin["body_pos_w"],
        body_quat_w=body_kin["body_quat_w"],
        body_lin_vel_w=body_kin["body_lin_vel_w"],
        body_ang_vel_w=body_kin["body_ang_vel_w"],
    )
    print(f"\nSaved: {output_path}")
    print(f"  T={T}, fps={fps}")
    print(f"  joint_pos: {joint_pos_all.shape}")
    print(f"  joint_vel: {joint_vel_all.shape}")
    print(f"  body_pos_w: {body_kin['body_pos_w'].shape}")
    print(f"  joint_names ({len(joint_names)}): {joint_names}")
    print(f"  body_names ({len(body_names)}): {body_names}")


def main():
    parser = argparse.ArgumentParser(description="Retarget G1 trajectory to HU_D04 via Jacobian IK")
    parser.add_argument("input", help="Input G1 OmniRetarget NPZ file")
    parser.add_argument("output", help="Output HU_D04 holosoma NPZ file")
    parser.add_argument(
        "--g1-xml",
        default="/workspace/holosoma/src/holosoma_retargeting/holosoma_retargeting/models/g1/g1_29dof_spherehand.xml",
        help="G1 MuJoCo XML path (spherehand variant for left_sphere_hand_link)",
    )
    parser.add_argument(
        "--hu-d04-xml",
        default="/workspace/holosoma/src/holosoma/holosoma/data/robots/hu_d04/hu_d04_31dof.xml",
        help="HU_D04 31dof MuJoCo XML path",
    )
    parser.add_argument("--max-iters", type=int, default=100, help="Max IK iterations per frame")
    parser.add_argument("--tol", type=float, default=1e-4, help="IK convergence tolerance (m)")
    parser.add_argument("--trust-region", type=float, default=0.1, help="IK trust region (rad)")
    args = parser.parse_args()

    convert(args.input, args.output, args.g1_xml, args.hu_d04_xml,
            args.max_iters, args.tol, args.trust_region)


if __name__ == "__main__":
    main()
