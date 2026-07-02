#!/usr/bin/env python
"""Replay a holosoma motion npz file in MuJoCo viewer.

Supports both holosoma-format npz (pos-first qpos) and OmniRetarget-format
npz (quat-first qpos).

Usage:
    python replay_motion.py --motion <motion.npz> --robot-xml <robot.xml> [--fps 30] [--omniretarget]
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import mujoco
import mujoco.viewer as mjv
import numpy as np


def replay(motion_path: str, robot_xml: str, fps: float = 30.0, omniretarget: bool = False):
    """Replay motion in MuJoCo passive viewer."""
    data = np.load(motion_path, allow_pickle=True)
    print(f"Loading motion: {motion_path}")
    print(f"  keys: {list(data.keys())}")

    # Determine qpos source and format
    if "qpos" in data:
        # OmniRetarget format: [quat4, pos3, joints]
        qpos_all = data["qpos"]
        omniretarget = True
        print(f"  format: OmniRetarget (quat-first), qpos shape: {qpos_all.shape}")
    elif "joint_pos" in data:
        # Holosoma format: [pos3, quat4, joints]
        qpos_all = data["joint_pos"]
        print(f"  format: holosoma (pos-first), joint_pos shape: {qpos_all.shape}")
    else:
        raise ValueError(f"No qpos or joint_pos in {motion_path}")

    fps = float(data["fps"]) if "fps" in data else fps
    if hasattr(fps, "__len__"):
        fps = float(fps[0]) if len(fps) > 0 else 30.0
    T = qpos_all.shape[0]
    dt = 1.0 / fps
    print(f"  frames: {T}, fps: {fps}, duration: {T*dt:.2f}s")

    # Load robot model
    model = mujoco.MjModel.from_xml_path(robot_xml)
    mdata = mujoco.MjData(model)
    nq = model.nq
    print(f"  robot: nq={nq}, nbody={model.nbody}")

    # Check dimension match
    qpos_dim = qpos_all.shape[1]
    if qpos_dim < nq:
        # Need to insert head zeros for 31dof model (qpos_dim=36, nq=38)
        # head joints at qpos indices 22, 23
        print(f"  inserting head zeros: qpos_dim={qpos_dim} -> nq={nq}")
        qpos_expanded = np.zeros((T, nq))
        qpos_expanded[:, :22] = qpos_all[:, :22]
        qpos_expanded[:, 24:] = qpos_all[:, 22:]
        qpos_all = qpos_expanded
    elif qpos_dim > nq:
        print(f"  WARNING: qpos_dim={qpos_dim} > nq={nq}, truncating")
        qpos_all = qpos_all[:, :nq]

    # Convert OmniRetarget quat-first to MuJoCo pos-first
    if omniretarget and "qpos" in data:
        print(f"  converting quat-first -> pos-first (MuJoCo order)")
        qpos_mj = np.zeros_like(qpos_all)
        qpos_mj[:, :3] = qpos_all[:, 4:7]    # pos
        qpos_mj[:, 3:7] = qpos_all[:, :4]    # quat (wxyz)
        qpos_mj[:, 7:] = qpos_all[:, 7:]     # joints
        qpos_all = qpos_mj

    # Launch viewer
    print(f"\nLaunching MuJoCo viewer... (press ESC to quit)")
    with mjv.launch_passive(model, mdata, show_left_ui=False, show_right_ui=False) as viewer:
        viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_PERTFORCE] = 0
        viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = 0
        viewer.cam.distance = 3.0
        viewer.cam.elevation = -20.0
        viewer.cam.azimuth = 45.0

        frame = 0
        while viewer.is_running() and frame < T:
            step_start = time.time()

            # Set qpos and forward
            mdata.qpos[:] = qpos_all[frame]
            mdata.qvel[:] = 0
            mujoco.mj_forward(model, mdata)

            viewer.sync()
            frame += 1

            if frame % 30 == 0:
                print(f"  frame {frame}/{T}")

            # Sleep to maintain fps
            elapsed = time.time() - step_start
            if elapsed < dt:
                time.sleep(dt - elapsed)

        # Hold last frame
        print("Motion ended. Press ESC to close.")
        while viewer.is_running():
            viewer.sync()
            time.sleep(0.03)


def main():
    parser = argparse.ArgumentParser(description="Replay holosoma/OmniRetarget motion in MuJoCo viewer")
    parser.add_argument("--motion", "-m", required=True, help="Path to motion .npz file")
    parser.add_argument("--robot-xml", "-r", required=True, help="Path to robot MuJoCo .xml file")
    parser.add_argument("--fps", type=float, default=30.0, help="Playback FPS (default: from motion file)")
    parser.add_argument("--omniretarget", action="store_true", help="Force OmniRetarget quat-first format")
    args = parser.parse_args()

    replay(args.motion, args.robot_xml, args.fps, args.omniretarget)


if __name__ == "__main__":
    main()
