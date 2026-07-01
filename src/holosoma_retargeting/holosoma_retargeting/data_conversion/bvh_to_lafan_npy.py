#!/usr/bin/env python
"""Convert BVH motion file to LAFAN-format .npy for the retargeter.

Parses a BVH file, computes world-space joint positions for each frame,
and extracts the 22 LAFAN_DEMO_JOINTS in the correct order. The output
is a (T, 22, 3) array in y-up coordinates (the retargeter's lafan loader
applies transform_y_up_to_z_up internally).

Usage:
    python bvh_to_lafan_npy.py input.bvh output.npy [--downsample N]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


LAFAN_DEMO_JOINTS = [
    "Hips", "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase",
    "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
    "Spine", "Spine1", "Spine2", "Neck", "Head",
    "RightShoulder", "RightArm", "RightForeArm", "RightHand",
    "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand",
]


class BVHJoint:
    """A joint in the BVH hierarchy."""

    def __init__(self, name: str, offset: np.ndarray, channels: list[str]):
        self.name = name
        self.offset = offset  # (3,) local offset from parent
        self.channels = channels  # list of channel names like ["Xposition", "Yposition", ...]
        self.children: list["BVHJoint"] = []
        self.parent: "BVHJoint | None" = None
        # Index into the frame data array for this joint's channels
        self.channel_idx: list[int] = []


def parse_bvh(bvh_path: str) -> tuple[BVHJoint, int, float, np.ndarray]:
    """Parse a BVH file.

    Returns:
        root_joint: The root BVHJoint
        n_frames: Number of motion frames
        frame_time: Time per frame (seconds)
        motion_data: (n_frames, n_channels) array of channel values
    """
    with open(bvh_path) as f:
        lines = f.readlines()

    # Parse hierarchy
    root = None
    channel_count = 0
    joint_stack: list[BVHJoint] = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("ROOT") or line.startswith("JOINT"):
            name = line.split()[1]
            # Read offset and channels (next few lines)
            j = i + 1
            while j < len(lines) and "{" not in lines[j]:
                j += 1
            j += 1  # skip {
            offset = None
            channels = []
            while j < len(lines):
                jline = lines[j].strip()
                if jline.startswith("OFFSET"):
                    parts = jline.split()
                    offset = np.array([float(parts[1]), float(parts[2]), float(parts[3])])
                elif jline.startswith("CHANNELS"):
                    parts = jline.split()
                    n_ch = int(parts[1])
                    channels = parts[2:2 + n_ch]
                elif jline == "{" or jline == "":
                    pass
                else:
                    break
                j += 1

            joint = BVHJoint(name, offset, channels)
            if joint_stack:
                joint.parent = joint_stack[-1]
                joint_stack[-1].children.append(joint)
            else:
                root = joint

            # Check what comes next: more children or end of this joint
            # Look ahead for JOINT or }
            k = j
            while k < len(lines):
                kline = lines[k].strip()
                if kline.startswith("JOINT") or kline == "{":
                    joint_stack.append(joint)
                    i = k - 1  # will be incremented to k
                    break
                elif kline == "}":
                    i = k
                    break
                k += 1
            else:
                i = k
        elif line.startswith("End Site"):
            # Skip end site blocks
            while i < len(lines) and lines[i].strip() != "}":
                i += 1
        elif line == "MOTION":
            break
        i += 1

    # Assign channel indices
    def assign_channel_indices(joint: BVHJoint, start_idx: int) -> int:
        joint.channel_idx = list(range(start_idx, start_idx + len(joint.channels)))
        idx = start_idx + len(joint.channels)
        for child in joint.children:
            idx = assign_channel_indices(child, idx)
        return idx

    assign_channel_indices(root, 0)

    # Parse motion
    n_frames = int(lines[i + 1].split(":")[1].strip())
    frame_time = float(lines[i + 2].split(":")[1].strip())
    motion_data = []
    for f in range(n_frames):
        frame_line = lines[i + 3 + f].strip()
        motion_data.append([float(x) for x in frame_line.split()])
    motion_data = np.array(motion_data)

    return root, n_frames, frame_time, motion_data


def compute_joint_positions(joint: BVHJoint, frame_data: np.ndarray, parent_transform: np.ndarray) -> dict[str, np.ndarray]:
    """Compute world-space positions for all joints in one frame.

    Uses forward kinematics: applies local rotation + offset to parent transform.

    Args:
        joint: The root joint
        frame_data: (n_channels,) array of channel values for this frame
        parent_transform: (4, 4) homogeneous transform of parent

    Returns:
        dict mapping joint name -> world position (3,)
    """
    # Extract this joint's channel values
    ch_vals = frame_data[joint.channel_idx]

    # Build local transform
    local_pos = joint.offset.copy()
    local_rot = np.eye(3)

    # Parse channels (BVH order matters: position channels first for root, then rotation)
    pos_channels = []
    rot_channels = []
    for i, ch in enumerate(joint.channels):
        if "position" in ch:
            pos_channels.append((ch, ch_vals[i]))
        elif "rotation" in ch:
            rot_channels.append((ch, ch_vals[i]))

    # Apply position channels (only root has position)
    for ch, val in pos_channels:
        if "X" in ch:
            local_pos[0] += val
        elif "Y" in ch:
            local_pos[1] += val
        elif "Z" in ch:
            local_pos[2] += val

    # Apply rotation channels (Euler angles in degrees, BVH order: Z, X, Y typically)
    # BVH rotation order is specified by the channel order
    for ch, val in rot_channels:
        angle = np.radians(val)
        if "X" in ch:
            R = np.array([[1, 0, 0], [0, np.cos(angle), -np.sin(angle)], [0, np.sin(angle), np.cos(angle)]])
        elif "Y" in ch:
            R = np.array([[np.cos(angle), 0, np.sin(angle)], [0, 1, 0], [-np.sin(angle), 0, np.cos(angle)]])
        elif "Z" in ch:
            R = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
        # BVH applies rotations in the order they appear in CHANNELS
        local_rot = local_rot @ R

    # Build local homogeneous transform
    local_transform = np.eye(4)
    local_transform[:3, 3] = local_pos
    local_transform[:3, :3] = local_rot

    # World transform
    world_transform = parent_transform @ local_transform
    world_pos = world_transform[:3, 3]

    positions = {joint.name: world_pos}
    for child in joint.children:
        positions.update(compute_joint_positions(child, frame_data, world_transform))

    return positions


def convert_bvh_to_npy(bvh_path: str, output_path: str, downsample: int = 1):
    """Convert BVH to LAFAN-format .npy."""
    print(f"Parsing BVH: {bvh_path}")
    root, n_frames, frame_time, motion_data = parse_bvh(bvh_path)
    print(f"  Frames: {n_frames}, Frame time: {frame_time}s, FPS: {1/frame_time:.1f}")
    print(f"  Root joint: {root.name}")
    print(f"  Channels: {motion_data.shape[1]}")

    # Downsample
    if downsample > 1:
        motion_data = motion_data[::downsample]
        n_frames = motion_data.shape[0]
        frame_time *= downsample
        print(f"  Downsampled by {downsample}: {n_frames} frames, FPS: {1/frame_time:.1f}")

    # Compute joint positions for all frames
    print("Computing joint positions...")
    all_positions = []
    for f in range(n_frames):
        positions = compute_joint_positions(root, motion_data[f], np.eye(4))
        all_positions.append(positions)

    # Check all LAFAN joints are present
    available_joints = set(all_positions[0].keys())
    missing = [j for j in LAFAN_DEMO_JOINTS if j not in available_joints]
    if missing:
        print(f"WARNING: Missing joints: {missing}")
        print(f"  Available: {sorted(available_joints)}")
        # For missing joints, use the closest available joint
        # Spine2 might be missing if BVH has Spine1 but not Spine2
        # Map Spine2 -> Spine1 if missing
        for j in missing:
            if j == "Spine2" and "Spine1" in available_joints:
                print(f"  Mapping Spine2 -> Spine1")
            elif j == "Spine" and "Spine1" in available_joints:
                print(f"  Mapping Spine -> Spine1")

    # Extract LAFAN joints in order
    joint_positions = np.zeros((n_frames, len(LAFAN_DEMO_JOINTS), 3))
    for f in range(n_frames):
        positions = all_positions[f]
        for j_idx, jname in enumerate(LAFAN_DEMO_JOINTS):
            if jname in positions:
                joint_positions[f, j_idx] = positions[jname]
            elif jname == "Spine2" and "Spine1" in positions:
                joint_positions[f, j_idx] = positions["Spine1"]
            elif jname == "Spine" and "Spine1" in positions:
                joint_positions[f, j_idx] = positions["Spine1"]
            # else: leave as zeros

    print(f"  Output shape: {joint_positions.shape}")
    print(f"  Units: m (converted from BVH cm)")
    print(f"  Coordinate: y-up (retargeter will convert to z-up)")

    # Convert cm to meters (BVH native unit is cm, retargeter expects meters)
    joint_positions = joint_positions / 100.0

    # Note: do NOT normalize/center the root position here.
    # The retargeter's transform_from_human_to_world computes an orientation from the
    # human-root-to-object vector; if we center the root at origin (where the dummy
    # object sits), that vector becomes zero-length and SVD fails.
    # The retargeter's preprocess_motion_data will subtract min toe Z for floor normalization.

    # Save
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_path, joint_positions)
    print(f"Saved: {output_path}")

    # Print summary stats
    print(f"\n  Joint position range (m):")
    print(f"    X: {joint_positions[:,:,0].min():.3f} to {joint_positions[:,:,0].max():.3f}")
    print(f"    Y: {joint_positions[:,:,1].min():.3f} to {joint_positions[:,:,1].max():.3f}")
    print(f"    Z: {joint_positions[:,:,2].min():.3f} to {joint_positions[:,:,2].max():.3f}")


def main():
    parser = argparse.ArgumentParser(description="Convert BVH to LAFAN-format .npy")
    parser.add_argument("input", help="Input BVH file")
    parser.add_argument("output", help="Output .npy file")
    parser.add_argument("--downsample", type=int, default=4,
                        help="Downsample factor (default: 4, to get ~22.5fps from 90fps)")
    args = parser.parse_args()

    convert_bvh_to_npy(args.input, args.output, args.downsample)


if __name__ == "__main__":
    main()
