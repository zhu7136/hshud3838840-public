#!/usr/bin/env python
"""Convert OmniRetarget (retargeter) output npz to holosoma training format.

The retargeter outputs qpos in Drake quat-first order: [quat(4), pos(3), joints(29)].
Holosoma expects pos-first MuJoCo order: [pos(3), quat(4), joints(31)] where
joints(31) includes head_yaw=0 and head_pitch=0 inserted after waist_pitch.

This script runs MuJoCo FK (mj_forward, no viewer) to compute real body
kinematics, and finite-difference velocities. No terrain penetration fix here
— use fix_ground_penetration.py afterwards.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import mujoco
import numpy as np


def convert(retargeter_npz: str, holosoma_xml: str, output: str, output_fps: int = 50):
    """Convert retargeter npz to holosoma format.

    Args:
        retargeter_npz: Path to retargeter output .npz with keys {qpos, fps, ...}
        holosoma_xml: Path to holosoma hu_d04.xml model file
        output: Path to output .npz
        output_fps: Target FPS (interpolated from input fps)
    """
    data = np.load(retargeter_npz, allow_pickle=True)
    qpos_ret = data["qpos"]  # (T, 36): [quat(4), pos(3), joints(29)]
    input_fps = int(data["fps"])
    T_in = qpos_ret.shape[0]
    print(f"Loaded: {retargeter_npz}")
    print(f"  qpos: {qpos_ret.shape}, fps={input_fps}, T={T_in}")

    # Convert quat-first [quat(4), pos(3), joints(29)] -> pos-first [pos(3), quat(4), joints(29)]
    quat = qpos_ret[:, :4]   # (T, 4) wxyz
    pos = qpos_ret[:, 4:7]   # (T, 3)
    joints29 = qpos_ret[:, 7:]  # (T, 29)

    # Insert head_yaw=0, head_pitch=0 after waist_pitch (index 14) to make 31 joints
    # 29 joints: [0:15] = legs(12) + waist(3), [15:29] = arms(14)
    joints31 = np.zeros((T_in, 31), dtype=np.float64)
    joints31[:, :15] = joints29[:, :15]   # legs + waist
    joints31[:, 15:17] = 0.0              # head_yaw, head_pitch (fixed joints = 0)
    joints31[:, 17:] = joints29[:, 15:]   # arms

    # Build pos-first qpos: [pos(3), quat(4), joints(31)]
    qpos_holosoma = np.concatenate([pos, quat, joints31], axis=1)  # (T, 38)

    # Interpolate to output_fps
    dt_in = 1.0 / input_fps
    duration = (T_in - 1) * dt_in
    dt_out = 1.0 / output_fps
    times = np.arange(0, duration, dt_out)
    T_out = len(times)
    print(f"  Interpolating to {output_fps} fps: {T_in} -> {T_out} frames")

    # Frame blend indices
    phase = times / duration
    idx0 = (phase * (T_in - 1)).astype(int)
    idx1 = np.minimum(idx0 + 1, T_in - 1)
    blend = phase * (T_in - 1) - idx0

    def lerp(a, b, t):
        return a * (1 - t) + b * t

    def slerp(q0, q1, t):
        """Slerp for wxyz quaternions. q0, q1: (T,4), t: (T,)."""
        q0 = q0 / np.linalg.norm(q0, axis=1, keepdims=True)
        q1 = q1 / np.linalg.norm(q1, axis=1, keepdims=True)
        dot = np.sum(q0 * q1, axis=1)
        # Flip for shortest path
        flip = dot < 0
        q1[flip] = -q1[flip]
        dot = np.abs(dot)
        dot = np.clip(dot, -1.0, 1.0)
        theta = np.arccos(dot)
        sin_theta = np.sin(theta)
        close = sin_theta < 1e-8
        s0 = np.where(close, 1 - t, np.sin((1 - t) * theta) / (sin_theta + 1e-12))
        s1 = np.where(close, t, np.sin(t * theta) / (sin_theta + 1e-12))
        out = s0[:, None] * q0 + s1[:, None] * q1
        return out / np.linalg.norm(out, axis=1, keepdims=True)

    pos_interp = lerp(qpos_holosoma[idx0, :3], qpos_holosoma[idx1, :3], blend[:, None])
    quat_interp = slerp(qpos_holosoma[idx0, 3:7], qpos_holosoma[idx1, 3:7], blend)
    joints_interp = lerp(qpos_holosoma[idx0, 7:], qpos_holosoma[idx1, 7:], blend[:, None])
    qpos_interp = np.concatenate([pos_interp, quat_interp, joints_interp], axis=1)  # (T_out, 38)

    # Load holosoma MuJoCo model
    model = mujoco.MjModel.from_xml_path(holosoma_xml)
    mj_data = mujoco.MjData(model)
    print(f"  Model: nbody={model.nbody}, njnt={model.njnt}, nq={model.nq}, nv={model.nv}")

    # Get joint and body names
    joint_names_mj = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i) for i in range(model.njnt)]
    body_names_mj = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i) for i in range(model.nbody)]

    # Build joint index mapping: holosoma 31 joints -> MuJoCo 29 actuated joints
    # MuJoCo joint names (excluding free/floating base): 29 actuated joints
    actuated_joints_mj = [
        n for n in joint_names_mj
        if n is not None and n != "root" and "floating_base" not in n
    ]
    print(f"  Actuated joints in model: {len(actuated_joints_mj)}")

    # holosoma 31 joint names (with head)
    joint_names_31 = [
        "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
        "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
        "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
        "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
        "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
        "head_yaw_joint", "head_pitch_joint",
        "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint",
        "left_elbow_joint", "left_wrist_yaw_joint", "left_wrist_pitch_joint", "left_wrist_roll_joint",
        "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint",
        "right_elbow_joint", "right_wrist_yaw_joint", "right_wrist_pitch_joint", "right_wrist_roll_joint",
    ]

    # Map: for each of 31 holosoma joints, find its index in MuJoCo's actuated joints
    # head_yaw and head_pitch are not in MuJoCo model (fixed) -> skip
    dof_index_map = []  # 31 entries; None for head joints
    for jn in joint_names_31:
        if jn in actuated_joints_mj:
            dof_index_map.append(actuated_joints_mj.index(jn))
        else:
            dof_index_map.append(None)  # head joint, not in model
    print(f"  Joint map: {sum(1 for x in dof_index_map if x is not None)} mapped, {sum(1 for x in dof_index_map if x is None)} head (fixed)")

    # Run FK for each frame
    body_pos_w = np.zeros((T_out, model.nbody, 3), dtype=np.float64)
    body_quat_w = np.zeros((T_out, model.nbody, 4), dtype=np.float64)

    for t in range(T_out):
        # Set qpos: [pos(3), quat(4), 29 actuated joints]
        mj_data.qpos[:3] = qpos_interp[t, :3]
        mj_data.qpos[3:7] = qpos_interp[t, 3:7]
        # Map 31 holosoma joints to 29 MuJoCo joints (skip head)
        mj_joints = np.zeros(len(actuated_joints_mj), dtype=np.float64)
        for j31, j_mj in enumerate(dof_index_map):
            if j_mj is not None:
                mj_joints[j_mj] = qpos_interp[t, 7 + j31]
        mj_data.qpos[7:7 + len(actuated_joints_mj)] = mj_joints
        mujoco.mj_forward(model, mj_data)
        body_pos_w[t] = mj_data.xpos[:]
        body_quat_w[t] = mj_data.xquat[:]

    # Compute velocities via finite differences
    dt = dt_out
    # joint_vel: (T, 6+31) = [lin_vel(3), ang_vel(3), joint_vel(31)]
    joint_vel = np.zeros((T_out, 6 + 31), dtype=np.float64)
    # Root linear velocity
    joint_vel[:, :3] = np.gradient(qpos_interp[:, :3], dt, axis=0)
    # Joint velocities (31, including head=0)
    joint_vel[:, 6:] = np.gradient(qpos_interp[:, 7:], dt, axis=0)
    # Root angular velocity from quaternion differences
    for t in range(1, T_out - 1):
        q0 = qpos_interp[t - 1, 3:7]  # wxyz
        q1 = qpos_interp[t + 1, 3:7]
        q0_conj = np.array([q0[0], -q0[1], -q0[2], -q0[3]])
        # q_rel = q1 * q0_conj
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
        joint_vel[t, 3:6] = axis * angle / (2 * dt)
    joint_vel[0, 3:6] = joint_vel[1, 3:6]
    joint_vel[-1, 3:6] = joint_vel[-2, 3:6]

    # Body velocities
    body_lin_vel_w = np.gradient(body_pos_w, dt, axis=0)
    body_ang_vel_w = np.zeros_like(body_lin_vel_w)  # Keep zero or compute from body_quat_w

    # Compute body angular velocities from body_quat_w
    for t in range(1, T_out - 1):
        for b in range(model.nbody):
            q0 = body_quat_w[t - 1, b]
            q1 = body_quat_w[t + 1, b]
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
            body_ang_vel_w[t, b] = axis * angle / (2 * dt)
    body_ang_vel_w[0] = body_ang_vel_w[1]
    body_ang_vel_w[-1] = body_ang_vel_w[-2]

    # Report
    print(f"\n  Output: T={T_out}, fps={output_fps}")
    print(f"  joint_pos: {qpos_interp.shape}")
    print(f"  body_pos_w: {body_pos_w.shape}")
    print(f"  Root z range: {qpos_interp[:, 2].min():.4f} - {qpos_interp[:, 2].max():.4f}")

    # Save
    out = {
        "fps": np.array([output_fps]),
        "joint_names": np.array(joint_names_31, dtype=object),
        "body_names": np.array(body_names_mj, dtype=object),
        "joint_pos": qpos_interp,
        "joint_vel": joint_vel,
        "body_pos_w": body_pos_w,
        "body_quat_w": body_quat_w,
        "body_lin_vel_w": body_lin_vel_w,
        "body_ang_vel_w": body_ang_vel_w,
    }
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    np.savez(output, **out)
    print(f"  Saved: {output}")


def main():
    parser = argparse.ArgumentParser(description="Convert retargeter output to holosoma format")
    parser.add_argument("retargeter_npz", help="Path to retargeter output .npz")
    parser.add_argument("--model", default="src/holosoma/holosoma/data/robots/hu_d04/hu_d04.xml",
                        help="Path to holosoma hu_d04.xml")
    parser.add_argument("--output", "-o", required=True, help="Output .npz path")
    parser.add_argument("--fps", type=int, default=50, help="Output FPS")
    args = parser.parse_args()
    convert(args.retargeter_npz, args.model, args.output, args.fps)


if __name__ == "__main__":
    main()
