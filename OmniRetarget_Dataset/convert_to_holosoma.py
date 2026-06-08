#!/usr/bin/env python
"""Convert Drake qpos/fps npz to holosoma format.

Supports G1 and HU_D04 robots.
"""

import numpy as np

# Reference: holosoma/data/motions/g1_29dof/whole_body_tracking/motion_crawl_slope.npz
HOLONOMA_BODY_NAMES = [
    "world",
    "pelvis", "pelvis_contour_link", "left_hip_pitch_link", "left_hip_roll_link", "left_hip_yaw_link",
    "left_knee_link", "left_ankle_intermediate_1_link", "left_ankle_pitch_link", "left_ankle_roll_link",
    "left_ankle_roll_sphere_3_link", "left_ankle_roll_sphere_4_link", "left_ankle_roll_sphere_5_link",
    "left_ankle_roll_sphere_1_link", "left_ankle_roll_sphere_2_link",
    "right_hip_pitch_link", "right_hip_roll_link", "right_hip_yaw_link",
    "right_knee_link", "right_ankle_intermediate_1_link", "right_ankle_pitch_link", "right_ankle_roll_link",
    "right_ankle_roll_sphere_3_link", "right_ankle_roll_sphere_4_link", "right_ankle_roll_sphere_5_link",
    "right_ankle_roll_sphere_1_link", "right_ankle_roll_sphere_2_link",
    "waist_yaw_link", "waist_roll_link", "torso_link", "waist_support_link",
    "left_shoulder_pitch_link", "left_shoulder_roll_link", "left_shoulder_yaw_link",
    "left_elbow_link", "left_wrist_roll_link", "left_wrist_pitch_link", "left_wrist_yaw_link",
    "left_rubber_hand_link", "left_thumb_link", "left_pinky_link",
    "right_shoulder_pitch_link", "right_shoulder_roll_link", "right_shoulder_yaw_link",
    "right_elbow_link", "right_wrist_roll_link", "right_wrist_pitch_link", "right_wrist_yaw_link",
    "right_rubber_hand_link", "right_thumb_link", "right_pinky_link",
]

HOLONOMA_JOINT_NAMES = [
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

def drake_to_holosoma_joints(drake_joints: np.ndarray) -> np.ndarray:
    """Reorder Drake joints [29] to holosoma order [29].

    Drake order (from visualize.py qpos):
      [0:6]=L_leg, [6:12]=R_leg, [12:15]=waist, [15:25]=L_arm, [25:29]=R_arm
    Holosoma order (from motion_crawl_slope.npz):
      [0:6]=L_leg, [6:12]=R_leg, [12:15]=waist, [15:22]=L_arm, [22:29]=R_arm
    """
    holosoma_joints = np.zeros(29, dtype=np.float32)

    # Legs (0-11): same order
    holosoma_joints[0:12] = drake_joints[0:12]

    # Waist (12-14): Drake [yaw, pitch, roll] -> Holosoma [yaw, roll, pitch]
    holosoma_joints[12] = drake_joints[12]  # waist_yaw
    holosoma_joints[13] = drake_joints[14]  # waist_roll
    holosoma_joints[14] = drake_joints[13]  # waist_pitch

    # Left arm (15-21): Drake [15:20]=shoulder(3)+elbow+wrist_roll, [25]=wrist_pitch
    # Holosoma: shoulder(3)+elbow+wrist_roll+wrist_pitch+wrist_yaw (7 joints minus 2 finger = 5)
    holosoma_joints[15:20] = drake_joints[[15, 16, 17, 18, 19]]  # shoulder(3) + elbow + wrist_roll
    holosoma_joints[20] = drake_joints[25]  # wrist_pitch
    holosoma_joints[21] = 0.0  # wrist_yaw (Drake doesn't have this)

    # Right arm (22-28): Drake [20:25]=shoulder(3)+elbow+wrist_roll, [27]=wrist_pitch
    holosoma_joints[22:27] = drake_joints[[20, 21, 22, 23, 24]]  # shoulder(3) + elbow + wrist_roll
    holosoma_joints[27] = drake_joints[27]  # wrist_pitch
    holosoma_joints[28] = 0.0  # wrist_yaw (Drake doesn't have this)

    return holosoma_joints


# HU_D04 body and joint names (from URDF, without head joints)
HU_D04_BODY_NAMES = [
    "world",
    "base_link",
    "left_hip_pitch_link", "left_hip_roll_link", "left_hip_yaw_link",
    "left_knee_link", "left_ankle_pitch_link", "left_ankle_roll_link",
    "contact_foot_heel_L", "contact_foot_center_L", "contact_foot_tip_L",
    "right_hip_pitch_link", "right_hip_roll_link", "right_hip_yaw_link",
    "right_knee_link", "right_ankle_pitch_link", "right_ankle_roll_link",
    "contact_foot_heel_R", "contact_foot_center_R", "contact_foot_tip_R",
    "waist_yaw_link", "waist_roll_link", "waist_pitch_link",
    "left_shoulder_pitch_link", "left_shoulder_roll_link", "left_shoulder_yaw_link",
    "left_elbow_link", "left_wrist_yaw_link", "left_wrist_pitch_link", "left_wrist_roll_link",
    "left_hand_contact", "left_hand_manip",
    "right_shoulder_pitch_link", "right_shoulder_roll_link", "right_shoulder_yaw_link",
    "right_elbow_link", "right_wrist_yaw_link", "right_wrist_pitch_link", "right_wrist_roll_link",
    "right_hand_contact", "right_hand_manip",
]

HU_D04_29DOF_JOINT_NAMES = [
    "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
    "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
    "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
    "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
    "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint",
    "left_elbow_joint", "left_wrist_yaw_joint", "left_wrist_pitch_joint", "left_wrist_roll_joint",
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint",
    "right_elbow_joint", "right_wrist_yaw_joint", "right_wrist_pitch_joint", "right_wrist_roll_joint",
]

HU_D04_31DOF_JOINT_NAMES = [
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


def hu_d04_drake_to_holosoma_joints(drake_joints: np.ndarray, with_head: bool = False) -> np.ndarray:
    """Reorder HU_D04 Drake joints to holosoma order.

    Assumes Drake output matches URDF joint order (same as holosoma for HU_D04).
    If with_head=True, expects 31 joints and strips head joints to return 29.
    """
    if with_head and len(drake_joints) == 31:
        # Strip head_yaw (index 15) and head_pitch (index 16)
        return np.delete(drake_joints, [15, 16]).astype(np.float32)
    elif len(drake_joints) == 29:
        return drake_joints.astype(np.float32)
    else:
        raise ValueError(f"Unexpected HU_D04 joint count: {len(drake_joints)}")


def convert_drake_to_holosoma(drake_npz_path: str, output_path: str = None):
    """Convert Drake qpos/fps format to holosoma format."""
    data = np.load(drake_npz_path, allow_pickle=True)
    qpos = data['qpos']  # [T, 36] = [T, 7 (base) + 29 (joints)]
    fps = float(data['fps'])

    T, dof = qpos.shape

    # Reorder joints from Drake to Holosoma format
    joint_pos_holosoma = np.zeros((T, 29), dtype=np.float32)
    joint_vel_holosoma = np.zeros((T, 29), dtype=np.float32)

    dt = 1.0 / fps
    for t in range(T):
        joint_pos_holosoma[t] = drake_to_holosoma_joints(qpos[t, 7:])

    # Compute velocities
    joint_vel_holosoma = np.gradient(joint_pos_holosoma, dt, axis=0)

    # Base pose (unchanged)
    base_xyz = qpos[:, :3].astype(np.float32)
    base_quat = qpos[:, 3:7].astype(np.float32)
    base_lin_vel = np.gradient(base_xyz, dt, axis=0).astype(np.float32)

    # Base angular velocity (approximate from waist joint velocity)
    base_ang_vel = np.zeros((T, 3), dtype=np.float32)
    for t in range(1, T - 1):
        base_ang_vel[t] = (qpos[t + 1, 7:10] - qpos[t - 1, 7:10]) / (2 * dt)

    # Concatenate: joint_pos = [base_xyz, base_quat, joints] = [T, 3+4+29=36]
    joint_pos = np.concatenate([base_xyz, base_quat, joint_pos_holosoma], axis=1)  # [T, 36]
    joint_vel = np.concatenate([base_lin_vel, base_ang_vel, joint_vel_holosoma], axis=1)  # [T, 35]

    # Body positions/velocities (all bodies at base frame for simplicity)
    # 51 bodies
    body_pos_w = np.tile(base_xyz[:, np.newaxis, :], (1, len(HOLONOMA_BODY_NAMES), 1)).astype(np.float32)
    body_quat_w = np.tile(base_quat[:, np.newaxis, :], (1, len(HOLONOMA_BODY_NAMES), 1)).astype(np.float32)
    body_lin_vel_w = np.tile(base_lin_vel[:, np.newaxis, :], (1, len(HOLONOMA_BODY_NAMES), 1)).astype(np.float32)
    body_ang_vel_w = np.tile(base_ang_vel[:, np.newaxis, :], (1, len(HOLONOMA_BODY_NAMES), 1)).astype(np.float32)

    out_path = output_path or drake_npz_path.replace('.npz', '_holosoma.npz')

    # Save with fixed-length Unicode strings
    np.savez(out_path,
        fps=np.float64(fps),
        joint_names=np.array(HOLONOMA_JOINT_NAMES, dtype='U32'),
        body_names=np.array(HOLONOMA_BODY_NAMES, dtype='U32'),
        joint_pos=joint_pos,
        joint_vel=joint_vel,
        body_pos_w=body_pos_w,
        body_quat_w=body_quat_w,
        body_lin_vel_w=body_lin_vel_w,
        body_ang_vel_w=body_ang_vel_w,
    )
    print(f"Converted: {drake_npz_path} -> {out_path}")
    print(f"  T={T}, fps={fps}, joint_pos={joint_pos.shape}, joint_vel={joint_vel.shape}")
    print(f"  body_names={len(HOLONOMA_BODY_NAMES)}, joint_names={len(HOLONOMA_JOINT_NAMES)}")


def convert_hu_d04_drake_to_holosoma(drake_npz_path: str, output_path: str = None, with_head: bool = False):
    """Convert HU_D04 Drake qpos/fps format to holosoma format."""
    data = np.load(drake_npz_path, allow_pickle=True)
    qpos = data['qpos']  # [T, 7+N]
    fps = float(data['fps'])

    T, dof = qpos.shape
    n_joints = dof - 7
    joint_names = HU_D04_31DOF_JOINT_NAMES if with_head else HU_D04_29DOF_JOINT_NAMES
    n_out = 29  # Always output 29 DOF (strip head if present)

    joint_pos_holosoma = np.zeros((T, n_out), dtype=np.float32)
    dt = 1.0 / fps

    for t in range(T):
        joint_pos_holosoma[t] = hu_d04_drake_to_holosoma_joints(qpos[t, 7:], with_head=(n_joints == 31))

    joint_vel_holosoma = np.gradient(joint_pos_holosoma, dt, axis=0)

    base_xyz = qpos[:, :3].astype(np.float32)
    base_quat = qpos[:, 3:7].astype(np.float32)
    base_lin_vel = np.gradient(base_xyz, dt, axis=0).astype(np.float32)
    base_ang_vel = np.zeros((T, 3), dtype=np.float32)
    for t in range(1, T - 1):
        base_ang_vel[t] = (base_xyz[t + 1] - base_xyz[t - 1]) / (2 * dt)

    joint_pos = np.concatenate([base_xyz, base_quat, joint_pos_holosoma], axis=1)  # [T, 36]
    joint_vel = np.concatenate([base_lin_vel, base_ang_vel, joint_vel_holosoma], axis=1)  # [T, 35]

    body_pos_w = np.tile(base_xyz[:, np.newaxis, :], (1, len(HU_D04_BODY_NAMES), 1)).astype(np.float32)
    body_quat_w = np.tile(base_quat[:, np.newaxis, :], (1, len(HU_D04_BODY_NAMES), 1)).astype(np.float32)
    body_lin_vel_w = np.tile(base_lin_vel[:, np.newaxis, :], (1, len(HU_D04_BODY_NAMES), 1)).astype(np.float32)
    body_ang_vel_w = np.tile(base_ang_vel[:, np.newaxis, :], (1, len(HU_D04_BODY_NAMES), 1)).astype(np.float32)

    out_path = output_path or drake_npz_path.replace('.npz', '_holosoma.npz')

    np.savez(out_path,
        fps=np.float64(fps),
        joint_names=np.array(joint_names, dtype='U32'),
        body_names=np.array(HU_D04_BODY_NAMES, dtype='U32'),
        joint_pos=joint_pos,
        joint_vel=joint_vel,
        body_pos_w=body_pos_w,
        body_quat_w=body_quat_w,
        body_lin_vel_w=body_lin_vel_w,
        body_ang_vel_w=body_ang_vel_w,
    )
    print(f"Converted: {drake_npz_path} -> {out_path}")
    print(f"  T={T}, fps={fps}, joint_pos={joint_pos.shape}, joint_vel={joint_vel.shape}")
    print(f"  body_names={len(HU_D04_BODY_NAMES)}, joint_names={len(joint_names)}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python convert_to_holosoma.py <input.npz> [output.npz] [--robot g1|hu_d04] [--with-head]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = None
    robot = "g1"
    with_head = False

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--robot" and i + 1 < len(args):
            robot = args[i + 1]
            i += 2
        elif args[i] == "--with-head":
            with_head = True
            i += 1
        elif output_path is None:
            output_path = args[i]
            i += 1
        else:
            i += 1

    if robot == "hu_d04":
        convert_hu_d04_drake_to_holosoma(input_path, output_path, with_head=with_head)
    else:
        convert_drake_to_holosoma(input_path, output_path)
