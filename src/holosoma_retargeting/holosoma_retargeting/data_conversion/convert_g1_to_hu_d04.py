#!/usr/bin/env python
"""Convert G1 OmniRetarget qpos NPZ to HU_D04 holosoma format.

Pipeline:
  1. Load G1 OmniRetarget NPZ (qpos [T,36] = [quat4, pos3, joints29], fps)
  2. Remap joints: G1 (29 DOF) -> HU_D04 (31 DOF)
     - Legs (0-12): direct copy
     - Waist (12-15): direct copy
     - Head (15-17): insert zeros
     - Shoulders+elbow (17-21, 24-28): direct copy from G1
     - Wrist (21-23, 28-30): reorder roll<->yaw
  3. Run MuJoCo FK on HU_D04_gmr model to compute body kinematics
  4. Save holosoma NPZ format
"""

import argparse
from pathlib import Path

import mujoco
import numpy as np


# G1 joint order (29 DOF) from OmniRetarget
G1_JOINT_NAMES = [
    "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
    "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
    "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
    "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
    "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint",
    "left_elbow_joint", "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint",
    "right_elbow_joint", "right_wrist_roll_joint", "right_wrist_pitch_joint", "right_wrist_yaw_joint",
]

# HU_D04 joint order (31 DOF) from gmr.xml
HU_D04_JOINT_NAMES = [
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


def remap_g1_to_hu_d04(g1_joints: np.ndarray) -> np.ndarray:
    """Remap G1 29-DOF joints to HU_D04 31-DOF joints.

    Args:
        g1_joints: shape [29] — G1 joint positions in G1 order

    Returns:
        hu_d04_joints: shape [31] — HU_D04 joint positions in HU_D04 order
    """
    hu_d04_joints = np.zeros(31, dtype=np.float64)

    # Legs (0-11): identical order
    hu_d04_joints[0:12] = g1_joints[0:12]

    # Waist (12-14): identical order
    hu_d04_joints[12:15] = g1_joints[12:15]

    # Head (15-16): insert zeros (G1 has no head joints)
    hu_d04_joints[15] = 0.0  # head_yaw
    hu_d04_joints[16] = 0.0  # head_pitch

    # Left shoulder + elbow (17-20): same as G1[15:19]
    hu_d04_joints[17:21] = g1_joints[15:19]

    # Left wrist (21-23): reorder
    # G1 order: [19]=wrist_roll, [20]=wrist_pitch, [21]=wrist_yaw
    # HU_D04 order: [21]=wrist_yaw, [22]=wrist_pitch, [23]=wrist_roll
    hu_d04_joints[21] = g1_joints[21]  # wrist_yaw <- G1 wrist_yaw
    hu_d04_joints[22] = g1_joints[20]  # wrist_pitch <- G1 wrist_pitch
    hu_d04_joints[23] = g1_joints[19]  # wrist_roll <- G1 wrist_roll

    # Right shoulder + elbow (24-27): same as G1[22:26]
    hu_d04_joints[24:28] = g1_joints[22:26]

    # Right wrist (28-30): reorder
    # G1 order: [26]=wrist_roll, [27]=wrist_pitch, [28]=wrist_yaw
    # HU_D04 order: [28]=wrist_yaw, [29]=wrist_pitch, [30]=wrist_roll
    hu_d04_joints[28] = g1_joints[28]  # wrist_yaw <- G1 wrist_yaw
    hu_d04_joints[29] = g1_joints[27]  # wrist_pitch <- G1 wrist_pitch
    hu_d04_joints[30] = g1_joints[26]  # wrist_roll <- G1 wrist_roll

    return hu_d04_joints


def world_body_velocities(model, data):
    """Per-body COM velocities in the world frame.

    Returns:
        lin_w: (nbody, 3) linear velocities in world coords
        ang_w: (nbody, 3) angular velocities in world coords
    """
    v = np.zeros((model.nbody, 6))
    for b in range(model.nbody):
        mujoco.mj_objectVelocity(
            model, data, mujoco.mjtObj.mjOBJ_BODY, b, v[b], 0,
        )
    return v[:, 3:6], v[:, 0:3]


def convert(input_path: str, output_path: str, xml_path: str):
    """Convert G1 OmniRetarget NPZ to HU_D04 holosoma NPZ."""
    # Load G1 data
    data = np.load(input_path)
    qpos_g1 = data["qpos"]  # [T, 36] = [quat4, pos3, joints29]
    fps = float(data["fps"])
    T = qpos_g1.shape[0]
    print(f"Loaded {input_path}: T={T}, fps={fps}, qpos shape={qpos_g1.shape}")

    # Load HU_D04 MuJoCo model
    model = mujoco.MjModel.from_xml_path(xml_path)
    d = mujoco.MjData(model)
    print(f"Loaded HU_D04 model: nbody={model.nbody}, nu={model.nu}, nv={model.nv}")

    # Extract body and joint names from model
    body_names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i) for i in range(model.nbody)]
    joint_names = []
    for i in range(model.njnt):
        if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_FREE:
            continue
        joint_names.append(mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i))

    # Build dof_index_list: mapping from HU_D04 joint order to MuJoCo joint order
    mujoco_joint_names = []
    for i in range(model.njnt):
        if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_FREE:
            continue
        mujoco_joint_names.append(mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i))
    dof_index_list = [HU_D04_JOINT_NAMES.index(name) for name in mujoco_joint_names]
    print(f"MuJoCo joint order -> HU_D04 index mapping: {dof_index_list}")

    # Prepare output arrays
    joint_pos_all = np.zeros((T, 38), dtype=np.float64)  # 7 root + 31 joints
    joint_vel_all = np.zeros((T, 37), dtype=np.float64)  # 6 root + 31 joints
    body_pos_w = np.zeros((T, model.nbody, 3), dtype=np.float64)
    body_quat_w = np.zeros((T, model.nbody, 4), dtype=np.float64)
    body_lin_vel_w = np.zeros((T, model.nbody, 3), dtype=np.float64)
    body_ang_vel_w = np.zeros((T, model.nbody, 3), dtype=np.float64)

    dt = 1.0 / fps

    for t in range(T):
        # Extract G1 base and joints
        # OmniRetarget qpos format: [quat4(wxyz), pos3, joints29]
        base_quat = qpos_g1[t, :4]  # wxyz
        base_pos = qpos_g1[t, 4:7]
        g1_joints = qpos_g1[t, 7:]

        # Remap to HU_D04
        hu_d04_joints = remap_g1_to_hu_d04(g1_joints)

        # Set MuJoCo state: qpos = [pos3, quat4(wxyz), joints31]
        # Note: MuJoCo quat convention is wxyz, same as OmniRetarget
        d.qpos[:3] = base_pos
        d.qpos[3:7] = base_quat
        d.qpos[7:] = hu_d04_joints

        # Zero velocities for FK (we'll compute from finite differences)
        d.qvel[:] = 0.0

        # Forward kinematics
        mujoco.mj_forward(model, d)

        # Store joint positions (holosoma format: [pos3, quat4(wxyz), joints31])
        joint_pos_all[t, :3] = base_pos
        joint_pos_all[t, 3:7] = base_quat
        joint_pos_all[t, 7:] = hu_d04_joints

        # Store body kinematics
        body_pos_w[t] = d.xpos[:].copy()
        body_quat_w[t] = d.xquat[:].copy()

        # Compute body velocities
        lin_w, ang_w = world_body_velocities(model, d)
        body_lin_vel_w[t] = lin_w
        body_ang_vel_w[t] = ang_w

    # Compute joint velocities via finite differences
    # Root linear velocity
    joint_vel_all[:, :3] = np.gradient(joint_pos_all[:, :3], dt, axis=0)
    # Root angular velocity (from quaternion derivative)
    for t in range(T):
        if t == 0:
            joint_vel_all[t, 3:6] = 0.0
        elif t == T - 1:
            joint_vel_all[t, 3:6] = joint_vel_all[t - 1, 3:6]
        else:
            # Approximate angular velocity from quaternion difference
            q_prev = joint_pos_all[t - 1, 3:7]
            q_next = joint_pos_all[t + 1, 3:7]
            # Simple approximation: use base angular velocity from MuJoCo
            # Actually, let's just use finite diff on euler angles
            joint_vel_all[t, 3:6] = 0.0  # Will be overwritten below

    # Use MuJoCo's computed body angular velocity for root (body 0 = world, body 1 = base_link)
    # Actually, for root angular velocity, we need to compute from quaternion sequence
    # Let's use a simpler approach: compute from quaternion differences
    for t in range(1, T - 1):
        q0 = joint_pos_all[t - 1, 3:7]  # wxyz
        q1 = joint_pos_all[t + 1, 3:7]  # wxyz
        # q_rel = q1 * q0^{-1}
        q0_conj = np.array([q0[0], -q0[1], -q0[2], -q0[3]])
        w0, x0, y0, z0 = q1
        w1, x1, y1, z1 = q0_conj
        q_rel = np.array([
            w0*w1 - x0*x1 - y0*y1 - z0*z1,
            w0*x1 + x0*w1 + y0*z1 - z0*y1,
            w0*y1 - x0*z1 + y0*w1 + z0*x1,
            w0*z1 + x0*y1 - y0*x1 + z0*w1,
        ])
        # Normalize
        q_rel = q_rel / (np.linalg.norm(q_rel) + 1e-10)
        # Convert to axis-angle
        w = np.clip(q_rel[0], -1.0, 1.0)
        angle = 2.0 * np.arccos(w)
        s = np.sqrt(max(0.0, 1.0 - w * w))
        if s > 1e-8:
            axis = q_rel[1:] / s
        else:
            axis = np.zeros(3)
        joint_vel_all[t, 3:6] = axis * angle / (2.0 * dt)

    # Fill endpoints
    joint_vel_all[0, 3:6] = joint_vel_all[1, 3:6]
    joint_vel_all[-1, 3:6] = joint_vel_all[-2, 3:6]

    # Joint velocities (finite differences)
    joint_vel_all[:, 6:] = np.gradient(joint_pos_all[:, 7:], dt, axis=0)

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
        body_pos_w=body_pos_w,
        body_quat_w=body_quat_w,
        body_lin_vel_w=body_lin_vel_w,
        body_ang_vel_w=body_ang_vel_w,
    )
    print(f"\nSaved: {output_path}")
    print(f"  T={T}, fps={fps}")
    print(f"  joint_pos: {joint_pos_all.shape}")
    print(f"  joint_vel: {joint_vel_all.shape}")
    print(f"  body_pos_w: {body_pos_w.shape}")
    print(f"  body_quat_w: {body_quat_w.shape}")
    print(f"  joint_names ({len(joint_names)}): {joint_names}")
    print(f"  body_names ({len(body_names)}): {body_names}")


def main():
    parser = argparse.ArgumentParser(description="Convert G1 OmniRetarget NPZ to HU_D04 holosoma NPZ")
    parser.add_argument("input", help="Input G1 OmniRetarget NPZ file")
    parser.add_argument("output", help="Output HU_D04 holosoma NPZ file")
    parser.add_argument(
        "--xml",
        default=None,
        help="HU_D04 MuJoCo XML path (default: auto-detect from holosoma data/robots)",
    )
    args = parser.parse_args()

    if args.xml is None:
        # Auto-detect
        holosoma_root = Path(__file__).resolve().parents[3]
        args.xml = str(holosoma_root / "src" / "holosoma" / "holosoma" / "data" / "robots" / "hu_d04" / "hu_d04_31dof.xml")

    convert(args.input, args.output, args.xml)


if __name__ == "__main__":
    main()
