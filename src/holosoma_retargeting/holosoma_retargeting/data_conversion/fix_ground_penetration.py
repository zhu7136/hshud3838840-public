#!/usr/bin/env python
"""Post-process holosoma motion npz to fix terrain penetration.

For each frame, queries the terrain mesh height at each foot body's XY
position. If any foot z is below the terrain surface, shifts the entire
frame's root z up so the lowest foot sits on the terrain surface.

This prevents physics jitter during replay/training caused by foot-terrain
penetration (both ground plane and climbing obstacles).

Usage:
    python fix_ground_penetration.py <motion.npz> --terrain <terrain.obj> [--foot-body-names ...] [--margin 0.0]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import trimesh


def query_terrain_heights(terrain: trimesh.Trimesh, xy_points: np.ndarray) -> np.ndarray:
    """Query terrain height (highest z) at each (x, y) position via ray casting.

    Args:
        terrain: terrain mesh (z-up)
        xy_points: (N, 2) array of x, y coordinates

    Returns:
        (N,) array of terrain z heights. -1.0 if no hit (off-mesh).
    """
    N = len(xy_points)
    ray_origins = np.zeros((N, 3))
    ray_origins[:, :2] = xy_points
    ray_origins[:, 2] = 10.0  # start from above
    ray_dirs = np.zeros((N, 3))
    ray_dirs[:, 2] = -1.0

    locations, index_ray, index_tri = terrain.ray.intersects_location(ray_origins, ray_dirs)

    terrain_z = np.full(N, -1.0)
    for i, r in enumerate(index_ray):
        z = locations[i, 2]
        if z > terrain_z[r]:
            terrain_z[r] = z
    return terrain_z


def fix_ground_penetration(
    motion_path: str,
    terrain_path: str | None = None,
    foot_body_names: list[str] | None = None,
    margin: float = 0.0,
    output_path: str | None = None,
):
    """Fix terrain penetration by shifting root z up for frames where feet penetrate.

    Args:
        motion_path: Path to holosoma motion npz
        terrain_path: Path to terrain .obj mesh (if None, only checks z >= margin)
        foot_body_names: List of foot body names to check
        margin: Safety margin above terrain (default: 0.0 = exactly on surface)
        output_path: Output path (default: overwrite input)
    """
    if foot_body_names is None:
        foot_body_names = [
            "contact_foot_tip_L", "contact_foot_tip_R",
            "contact_foot_heel_L", "contact_foot_heel_R",
            "contact_foot_center_L", "contact_foot_center_R",
        ]
    if output_path is None:
        output_path = motion_path

    data = dict(np.load(motion_path, allow_pickle=True))
    body_names = [str(n) for n in data["body_names"]]
    joint_pos = data["joint_pos"]  # (T, 7+N), root pos at [:3]
    body_pos_w = data["body_pos_w"]  # (T, B, 3)

    T = joint_pos.shape[0]
    print(f"Loading: {motion_path}")
    print(f"  T={T}, fps={data['fps']}, body_pos_w={body_pos_w.shape}")

    # Load terrain
    terrain = None
    if terrain_path is not None:
        print(f"Loading terrain: {terrain_path}")
        terrain = trimesh.load(terrain_path)
        print(f"  bounds: {terrain.bounds}, extents: {terrain.extents}")

    # Find foot body indices
    foot_indices = []
    for fn in foot_body_names:
        if fn in body_names:
            foot_indices.append(body_names.index(fn))
        else:
            print(f"  WARNING: foot body '{fn}' not found in body_names")
    print(f"  Foot bodies: {[body_names[i] for i in foot_indices]}")

    if not foot_indices:
        print("  ERROR: No foot bodies found, nothing to fix")
        return

    # For each frame, find terrain height at each foot XY, compute required z-shift
    z_shift = np.zeros(T)
    for t in range(T):
        foot_xy = body_pos_w[t, foot_indices, :2]  # (num_feet, 2)
        foot_z = body_pos_w[t, foot_indices, 2]  # (num_feet,)

        if terrain is not None:
            terrain_z = query_terrain_heights(terrain, foot_xy)  # (num_feet,)
            # For feet off-mesh, use ground level (0)
            terrain_z = np.where(terrain_z < 0, 0.0, terrain_z)
        else:
            terrain_z = np.zeros(len(foot_indices))

        # Required z: foot_z + shift >= terrain_z + margin
        # shift >= terrain_z + margin - foot_z
        required_shift = terrain_z + margin - foot_z
        z_shift[t] = max(0.0, required_shift.max())

    # Apply shift to root pos in joint_pos
    joint_pos_fixed = joint_pos.copy()
    joint_pos_fixed[:, 2] += z_shift

    # Apply shift to all body_pos_w z
    body_pos_w_fixed = body_pos_w.copy()
    body_pos_w_fixed[:, :, 2] += z_shift[:, None]

    # Recompute ALL velocities from the shifted positions (finite differences).
    # The z-shift changes per-frame, so the original velocities are now stale.
    # Failing to recompute causes sim.forward() to apply wrong velocities → jitter.
    dt = 1.0 / float(data["fps"])
    joint_vel = data["joint_vel"]  # (T, 6+N): [lin_vel3, ang_vel3, joint_velN]
    joint_vel_fixed = joint_vel.copy()
    # Root linear velocity: finite diff of root pos (joint_pos[:, :3])
    joint_vel_fixed[:, :3] = np.gradient(joint_pos_fixed[:, :3], dt, axis=0)
    # Joint velocities: finite diff of joint_pos[:, 7:]
    joint_vel_fixed[:, 6:] = np.gradient(joint_pos_fixed[:, 7:], dt, axis=0)
    # Root angular velocity: keep original (z-shift doesn't change orientation)
    # but recompute from quaternion differences for consistency
    for t in range(1, T - 1):
        q0 = joint_pos_fixed[t - 1, 3:7]  # wxyz
        q1 = joint_pos_fixed[t + 1, 3:7]
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
        joint_vel_fixed[t, 3:6] = axis * angle / (2 * dt)
    joint_vel_fixed[0, 3:6] = joint_vel_fixed[1, 3:6]
    joint_vel_fixed[-1, 3:6] = joint_vel_fixed[-2, 3:6]

    # Recompute body linear velocities from shifted body_pos_w
    body_lin_vel_fixed = data["body_lin_vel_w"].copy()
    body_lin_vel_fixed[:] = np.gradient(body_pos_w_fixed, dt, axis=0)
    # Body angular velocities: keep original (z-shift doesn't change body orientations)
    body_ang_vel_fixed = data["body_ang_vel_w"].copy()

    # Report
    n_shifted = (z_shift > 1e-6).sum()
    print(f"\n  Frames shifted: {n_shifted}/{T} ({100*n_shifted/T:.1f}%)")
    if n_shifted > 0:
        shifted = z_shift[z_shift > 1e-6]
        print(f"  Shift amount: mean={shifted.mean():.4f}m, max={z_shift.max():.4f}m")

    # Verify
    foot_z_after = body_pos_w_fixed[:, foot_indices, 2]
    if terrain is not None:
        # Re-check penetration after fix
        pen_count = 0
        max_pen = 0
        for t in range(T):
            foot_xy = body_pos_w_fixed[t, foot_indices, :2]
            foot_z = body_pos_w_fixed[t, foot_indices, 2]
            terrain_z = query_terrain_heights(terrain, foot_xy)
            terrain_z = np.where(terrain_z < 0, 0.0, terrain_z)
            pen = terrain_z + margin - foot_z
            if pen.max() > 0:
                pen_count += 1
                max_pen = max(max_pen, pen.max())
        print(f"  After fix: {pen_count} frames still penetrating, max pen={max_pen:.4f}m")
    else:
        print(f"  After fix: min foot z = {foot_z_after.min():.4f}m (target >= {margin})")

    # Update data dict
    data["joint_pos"] = joint_pos_fixed
    data["joint_vel"] = joint_vel_fixed
    data["body_pos_w"] = body_pos_w_fixed
    data["body_lin_vel_w"] = body_lin_vel_fixed
    data["body_ang_vel_w"] = body_ang_vel_fixed

    # Save
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez(output_path, **data)
    print(f"\nSaved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Fix terrain penetration in holosoma motion npz")
    parser.add_argument("motion", help="Path to motion .npz file")
    parser.add_argument("--terrain", "-t", default=None,
                        help="Path to terrain .obj mesh (if omitted, only checks z >= margin)")
    parser.add_argument("--foot-body-names", default=None,
                        help="Comma-separated foot body names (default: contact_foot_*)")
    parser.add_argument("--margin", type=float, default=0.0,
                        help="Safety margin above terrain (default: 0.0)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output path (default: overwrite input)")
    args = parser.parse_args()

    foot_names = args.foot_body_names.split(",") if args.foot_body_names else None
    fix_ground_penetration(args.motion, args.terrain, foot_names, args.margin, args.output)


if __name__ == "__main__":
    main()
