import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

data = np.load("robot-terrain/climb_13_z_scale_1.2.npz")
joints = data["human_joints"]  # (T, 53, 3)
fps = int(data["fps"])
print(f"Frames: {len(joints)}, Joints: {joints.shape[1]}, FPS: {fps}")

# skeleton connections (MuJoCo humanoid)
edges = [
    (0, 1), (0, 2), (0, 3),          # pelvis -> L/R hip, spine
    (3, 4), (4, 5),                   # spine -> torso -> chest
    (5, 6), (5, 7),                   # chest -> L/R shoulder
    (6, 8), (8, 10),                  # L arm
    (7, 9), (9, 11),                  # R arm
    (1, 12), (12, 13), (13, 14),      # L leg
    (2, 15), (15, 16), (16, 17),      # R leg
]
# filter valid edges
edges = [(a, b) for a, b in edges if a < joints.shape[1] and b < joints.shape[1]]

fig = plt.figure(figsize=(6, 5), dpi=80)
ax = fig.add_subplot(111, projection="3d")

def update(frame):
    ax.cla()
    j = joints[frame]
    ax.scatter(j[:, 0], j[:, 1], j[:, 2], c="blue", s=20)
    for a, b in edges:
        ax.plot([j[a, 0], j[b, 0]], [j[a, 1], j[b, 1]], [j[a, 2], j[b, 2]], "r-", linewidth=2)
    # set consistent axis limits
    ax.set_xlim(j[:, 0].min() - 0.5, j[:, 0].max() + 0.5)
    ax.set_ylim(j[:, 1].min() - 0.5, j[:, 1].max() + 0.5)
    ax.set_zlim(j[:, 2].min() - 0.5, j[:, 2].max() + 0.5)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title(f"Frame {frame}/{len(joints)-1}")
    # keep aspect ratio roughly equal
    ax.set_box_aspect([1, 1, 1])

# save a single frame as PNG for quick preview
update(0)
fig.savefig("climb_13_preview.png", dpi=80, bbox_inches="tight")
print("Saved preview to climb_13_preview.png")

# also save GIF
ani = FuncAnimation(fig, update, frames=min(len(joints), 100), interval=1000 // fps)
out_path = "climb_13_z_scale_1.2.gif"
ani.save(out_path, writer="pillow", fps=fps)
print(f"Saved to {out_path}")
